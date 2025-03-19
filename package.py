#!/usr/bin/env python3

import sys
import zipapp
from pathlib import Path


def _create_archive(name: str, files: list[str]) -> None:
    def file_filter(path: Path):
        return path in map(Path, files)

    zipapp.create_archive(
        source="scripts",
        target=f"{name}.pyz",
        interpreter="/usr/bin/env python3",
        main=f"{name}:main",
        filter=file_filter,
    )


def archiver() -> None:
    _create_archive("archiver", ["archiver.py", "common.py"])


def backupper() -> None:
    _create_archive(
        "backupper", ["backupper.py", "common.py", "archiver.py", "checksum.py"]
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        # TODO Make generic  # pylint: disable=fixme
        archiver()
        backupper()
