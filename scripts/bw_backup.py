import getpass
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import common
import requests

BASE_DIR = Path.cwd()

TMP_DIR = BASE_DIR / "tmp"
BACKUP_DIR = BASE_DIR / "out"

GITHUB_API = "https://api.github.com/repos/bitwarden/clients/releases"
REQUEST_TIMEOUT = 30


def sha256_file(path, chunk_size=1024 * 1024):
    """Return SHA-256 hash of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)

    return digest.hexdigest()


def run(command, env=None, timeout=120):
    """Run a command and return stdout."""

    try:
        result = subprocess.run(
            command,
            env=env,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Command failed:\n"
            f"  {' '.join(map(str, command))}\n\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
        ) from exc

    return result.stdout.strip()


def load_config():
    """Load configuration from bw-backup.json."""

    config = common.Config("bw-backup.json").get_config()

    required = ["vault_url", "client_id", "client_secret"]

    for key in required:
        if not config.get(key):
            raise RuntimeError(f"Missing '{key}' in bw-backup.json")

    return config


def get_platform_info():
    """Determine the Bitwarden CLI asset for this machine."""

    system = platform.system().lower()
    machine = platform.machine().lower()

    prefixes = {
        "linux": "linux",
        "darwin": "macos",
        "windows": "windows",
    }
    platform_name = prefixes.get(system)

    if platform_name is None:
        raise RuntimeError(f"Unsupported operating system: {system}")

    architectures = {
        "x86_64": "",
        "amd64": "",
        "aarch64": "arm64-",
        "arm64": "arm64-",
    }
    architecture_suffix = architectures.get(machine)

    if architecture_suffix is None:
        raise RuntimeError(f"Unsupported {platform_name} architecture: {machine}")

    executable = "bw.exe" if system == "windows" else "bw"
    return f"bw-oss-{platform_name}-{architecture_suffix}", executable


def get_latest_bw_asset():
    """Find the latest stable Bitwarden CLI release."""

    prefix, executable = get_platform_info()

    response = requests.get(GITHUB_API, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    releases = response.json()

    for release in releases:
        if release.get("draft"):
            continue

        if release.get("prerelease"):
            continue

        tag = release.get("tag_name", "")

        # CLI releases use cli-x.y.z tags.
        if not tag.startswith("cli-"):
            continue

        for asset in release.get("assets", []):
            name = asset["name"]

            if name.startswith(prefix) and name.endswith(".zip"):
                digest = asset.get("digest")

                if not digest:
                    raise RuntimeError(f"GitHub did not provide a digest for {name}")

                if not digest.startswith("sha256:"):
                    raise RuntimeError(f"Unexpected digest format for {name}: {digest}")

                return {
                    "version": tag,
                    "name": name,
                    "url": asset["browser_download_url"],
                    "sha256": digest.split(":", 1)[1],
                    "executable": executable,
                }

    raise RuntimeError(
        f"Could not find a Bitwarden CLI release for "
        f"{platform.system()} / {platform.machine()}"
    )


def safe_extract_zip(archive, destination):
    """
    Extract ZIP while preventing path traversal.
    """

    destination = destination.resolve()

    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            target = (destination / member.filename).resolve()

            if not str(target).startswith(str(destination) + os.sep):
                raise RuntimeError(f"Unsafe path in ZIP archive: {member.filename}")

        zf.extractall(destination)


def safe_filename(name):
    """Return a filesystem-safe filename component."""

    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return name or "unnamed"


def prepare_bw():
    """
    Download the latest Bitwarden CLI if necessary.

    The downloaded ZIP is verified against the SHA-256
    digest published by GitHub before it is extracted.
    """

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    version_file = TMP_DIR / "version"
    hash_file = TMP_DIR / "sha256"

    latest = get_latest_bw_asset()
    bw_path = TMP_DIR / latest["executable"]

    if bw_path.exists() and version_file.exists() and hash_file.exists():
        local_version = version_file.read_text().strip()
        expected_hash = hash_file.read_text().strip()

        if local_version == latest["version"]:
            print(f"📦 Bitwarden CLI {local_version} found")

            print("🔍 Verifying cached CLI...")

            actual_hash = sha256_file(bw_path)

            if actual_hash == expected_hash:
                print("✅ Cached CLI verified")

                return bw_path

            print("⚠️ Cached CLI hash mismatch, downloading again...")

    archive_path = TMP_DIR / latest["name"]

    print(f"🔨 Latest Bitwarden CLI: {latest['name']} ({latest['version']})")
    print("⬇️ Downloading Bitwarden CLI...")

    with requests.get(latest["url"], stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with archive_path.open("wb") as archive:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    archive.write(chunk)

    print("🔍 Verifying downloaded ZIP...")

    actual_hash = sha256_file(archive_path)

    if actual_hash.lower() != latest["sha256"].lower():
        archive_path.unlink(missing_ok=True)

        raise RuntimeError(
            "Bitwarden CLI SHA-256 verification FAILED!\n\n"
            f"Expected:\n{latest['sha256']}\n\n"
            f"Actual:\n{actual_hash}\n\n"
            "The downloaded file has been deleted."
        )

    print("✅ SHA-256 verification successful")

    bw_path.unlink(missing_ok=True)

    print("📦 Extracting Bitwarden CLI...")

    try:
        safe_extract_zip(archive_path, TMP_DIR)
    finally:
        archive_path.unlink(missing_ok=True)

    if not bw_path.exists():
        raise RuntimeError(
            f"Expected executable was not found after extraction: {bw_path}"
        )

    if os.name != "nt":
        mode = bw_path.stat().st_mode

        bw_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    executable_hash = sha256_file(bw_path)

    version_file.write_text(latest["version"])
    hash_file.write_text(executable_hash)

    print(f"✅ Bitwarden CLI {latest['version']} ready: {bw_path}")

    return bw_path


def create_backup(bw, config):
    """Create an encrypted Bitwarden JSON backup."""

    master_password = getpass.getpass("✍️ Vaultwarden master password: ")

    export_password = getpass.getpass("✍️ Backup encryption password: ")

    if not export_password:
        raise RuntimeError("Backup encryption password cannot be empty.")

    env = os.environ.copy()

    env["BW_CLIENTID"] = config["client_id"]
    env["BW_CLIENTSECRET"] = config["client_secret"]
    env["BW_MASTER_PASSWORD"] = master_password

    try:
        current_server = run(
            [
                str(bw),
                "config",
                "server",
            ],
            env=env,
        )

        if current_server.rstrip("/") != config["vault_url"].rstrip("/"):
            print("🌐 Changing Vaultwarden server...")
            run([str(bw), "logout"], env=env)
            run([str(bw), "config", "server", config["vault_url"]], env=env)

        status = json.loads(
            run(
                [
                    str(bw),
                    "status",
                ],
                env=env,
            )
        )

        if status["status"] == "unauthenticated":
            print("🔑 Logging in with API key...")
            run([str(bw), "login", "--apikey"], env=env)

        print("🔓 Unlocking vault...")

        unlock_command = [
            str(bw),
            "unlock",
            "--passwordenv",
            "BW_MASTER_PASSWORD",
            "--raw",
        ]

        try:
            session = run(unlock_command, env=env)
        except RuntimeError:
            print("🔐 Local login state is invalid, logging in again...")
            run([str(bw), "logout"], env=env)
            run([str(bw), "login", "--apikey"], env=env)
            session = run(unlock_command, env=env)

        if not session:
            raise RuntimeError("bw unlock did not return a session.")

        env["BW_SESSION"] = session

        master_password = None
        env.pop("BW_MASTER_PASSWORD", None)

        print("🔄 Synchronizing vault...")

        run(
            [
                str(bw),
                "sync",
            ],
            env=env,
        )

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # noqa: DTZ005

        organizations = json.loads(run([str(bw), "list", "organizations"], env=env))

        exports = [("personal", None)] + [
            (f"org-{safe_filename(organization['name'])}", organization["id"])
            for organization in organizations
        ]

        print("💾 Creating encrypted backups...")

        for name, organization_id in exports:
            output = BACKUP_DIR / f"vault-{timestamp}-{name}.json"
            command = [
                str(bw),
                "export",
                "--format",
                "encrypted_json",
                "--password",
                export_password,
                "--output",
                str(output),
            ]
            if organization_id:
                command.extend(["--organizationid", organization_id])

            run(command, env=env)

            if output.stat().st_size == 0:
                raise RuntimeError(f"Backup file is empty: {output}")

            print(f"✅ Backup successfully created: {output}")

        export_password = None

    finally:
        print("🔒 Locking Bitwarden vault...")

        try:
            run(
                [
                    str(bw),
                    "lock",
                ],
                env=env,
            )

            print("✅ Vault locked")

        except Exception as exc:  # noqa: BLE001
            print(
                f"⚠️ Could not lock vault: {exc}",
                file=sys.stderr,
            )

        env.pop("BW_MASTER_PASSWORD", None)
        env.pop("BW_SESSION", None)

        master_password = None
        export_password = None


def main():
    bw = prepare_bw()
    config = load_config()
    create_backup(bw, config)


if __name__ == "__main__":
    main()
