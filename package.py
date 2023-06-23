#!/usr/bin/env python3

from pathlib import Path
import sys
import zipapp


def archiver() -> None:
    def archive_filter(path: Path):
        return path in map(Path, [
            'archiver.py',
            'common.py'
        ])

    zipapp.create_archive(
        source='scripts',
        target='archiver.pyz',
        interpreter='/usr/bin/env python3',
        main='archiver:main',
        filter=archive_filter
    )


if __name__ == '__main__':
    globals()[sys.argv[1]]()
