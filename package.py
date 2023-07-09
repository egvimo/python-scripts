#!/usr/bin/env python3

from pathlib import Path
import sys
import zipapp


def _create_archive(name: str, files: list[str]) -> None:
    def file_filter(path: Path):
        return path in map(Path, files)

    zipapp.create_archive(
        source='scripts',
        target=f"{name}.pyz",
        interpreter='/usr/bin/env python3',
        main=f"{name}:main",
        filter=file_filter
    )


def archiver() -> None:
    _create_archive('archiver', ['archiver.py', 'common.py'])


def backup() -> None:
    _create_archive('backup', [
        'backup.py',
        'common.py',
        'archiver.py',
        'checksum.py'
    ])


if __name__ == '__main__':
    globals()[sys.argv[1]]()
