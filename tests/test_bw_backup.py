import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts import bw_backup


def test_sha256_file(tmp_path: Path):
    path = tmp_path / "file"
    path.write_bytes(b"backup data")

    assert bw_backup.sha256_file(path) == hashlib.sha256(b"backup data").hexdigest()


@pytest.mark.parametrize(
    ("system", "machine", "expected_prefix", "expected_executable"),
    [
        ("Linux", "x86_64", "bw-oss-linux-", "bw"),
        ("Darwin", "arm64", "bw-oss-macos-arm64-", "bw"),
        ("Windows", "AMD64", "bw-oss-windows-", "bw.exe"),
    ],
)
def test_get_platform_info(
    monkeypatch: pytest.MonkeyPatch,
    system: str,
    machine: str,
    expected_prefix: str,
    expected_executable: str,
):
    monkeypatch.setattr(bw_backup.platform, "system", lambda: system)
    monkeypatch.setattr(bw_backup.platform, "machine", lambda: machine)

    assert bw_backup.get_platform_info() == (expected_prefix, expected_executable)


def test_get_platform_info_rejects_unknown_architecture(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(bw_backup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(bw_backup.platform, "machine", lambda: "sparc")

    with pytest.raises(RuntimeError, match="Unsupported linux architecture"):
        bw_backup.get_platform_info()


def test_get_latest_bw_asset_skips_non_cli_and_prereleases(
    monkeypatch: pytest.MonkeyPatch,
):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"tag_name": "v1.0.0", "assets": []},
                {"tag_name": "cli-v2.0.0", "prerelease": True, "assets": []},
                {
                    "tag_name": "cli-v3.0.0",
                    "assets": [
                        {
                            "name": "bw-oss-linux-x64.zip",
                            "digest": "sha256:wrong-architecture",
                        },
                        {
                            "name": "bw-oss-linux-arm64-test.zip",
                            "digest": "sha256:expected",
                            "browser_download_url": "https://example.test/bw.zip",
                        },
                    ],
                },
            ]

    monkeypatch.setattr(
        bw_backup,
        "get_platform_info",
        lambda: ("bw-oss-linux-arm64-", "bw"),
    )
    monkeypatch.setattr(bw_backup.requests, "get", lambda *args, **kwargs: Response())

    assert bw_backup.get_latest_bw_asset() == {
        "version": "cli-v3.0.0",
        "name": "bw-oss-linux-arm64-test.zip",
        "url": "https://example.test/bw.zip",
        "sha256": "expected",
        "executable": "bw",
    }


def test_safe_extract_zip_rejects_path_traversal(tmp_path: Path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("../outside.txt", "not safe")

    with pytest.raises(RuntimeError, match="Unsafe path"):
        bw_backup.safe_extract_zip(archive, tmp_path / "destination")


def test_prepare_bw_uses_verified_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    executable = tmp_path / "bw"
    executable.write_bytes(b"verified cli")
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    (tmp_path / "version").write_text("cli-v1.0.0")
    (tmp_path / "sha256").write_text(digest)

    monkeypatch.setattr(bw_backup, "TMP_DIR", tmp_path)
    monkeypatch.setattr(
        bw_backup,
        "get_latest_bw_asset",
        lambda: {"version": "cli-v1.0.0", "executable": "bw"},
    )

    assert bw_backup.prepare_bw() == executable


def test_create_backup_reuses_authenticated_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    commands = []

    def fake_run(command, env=None):
        commands.append(command)
        if command[1:] == ["config", "server"]:
            return "https://vault.example.com"
        if command[1:] == ["status"]:
            return json.dumps({"status": "locked"})
        if command[1:] == ["list", "organizations"]:
            return json.dumps([{"id": "org-id", "name": "Example / Org"}])
        if command[1:] == ["unlock", "--passwordenv", "BW_MASTER_PASSWORD", "--raw"]:
            return "session"
        if command[1] == "export":
            Path(command[command.index("--output") + 1]).write_bytes(
                b"encrypted backup"
            )
        return ""

    monkeypatch.setattr(bw_backup, "run", fake_run)
    monkeypatch.setattr(bw_backup.getpass, "getpass", lambda prompt: "password")
    monkeypatch.setattr(bw_backup, "bw", Path("bw"), raising=False)
    monkeypatch.setattr(bw_backup, "BACKUP_DIR", tmp_path)

    monkeypatch.setattr(
        bw_backup,
        "datetime",
        type(
            "DateTime",
            (),
            {
                "now": staticmethod(
                    lambda: type(
                        "Timestamp", (), {"strftime": lambda self, _: "test"}
                    )()
                )
            },
        ),
    )

    bw_backup.create_backup(
        Path("bw"),
        {
            "vault_url": "https://vault.example.com/",
            "client_id": "client",
            "client_secret": "secret",
        },
    )

    assert not any(command[1:] == ["logout"] for command in commands)
    assert not any(command[1:] == ["login", "--apikey"] for command in commands)
    assert any(command[1:] == ["lock"] for command in commands)
    exports = [command for command in commands if command[1] == "export"]
    assert len(exports) == 2
    assert exports[1][exports[1].index("--organizationid") + 1] == "org-id"
    assert (tmp_path / "vault-test-org-Example-Org.json").exists()


def test_prepare_bw_with_live_release_and_binary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(bw_backup, "TMP_DIR", tmp_path)

    executable = bw_backup.prepare_bw()
    result = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert executable.is_file()
    assert result.stdout.strip()
