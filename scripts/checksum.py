#!/usr/bin/env python3

import hashlib
import os
from argparse import ArgumentParser, Namespace
from typing import Iterator


def _create_argument_parser() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        description="Generate checksum of files or folders"
    )
    parser.add_argument(
        "targets", nargs="+", help="files or directories to generate checksum for"
    )
    return parser


def _checksum_files(sha, file_path, files) -> None:
    for filename in files:
        file = os.path.join(file_path, filename)
        filetype: str = "f"
        filesize: int = 0
        mod_time: float = 0.0

        if os.path.islink(file):
            filetype = "l"
        elif os.path.isdir(file):
            filetype = "d"
            mod_time = os.path.getmtime(file)
        else:
            stat = os.stat(file)
            filesize = stat.st_size
            mod_time = stat.st_mtime

        sha.update(f"{file}|{filetype}|{filesize}|{mod_time}".encode())


def generate(targets: list[str]) -> Iterator[tuple[str, str]]:
    for target in targets:
        normpath = os.path.normpath(target)
        sha = hashlib.sha1(usedforsecurity=False)
        for dirpath, dirnames, filenames in os.walk(normpath):
            _checksum_files(sha, dirpath, sorted(dirnames + filenames))
        yield normpath, sha.hexdigest()


def print_result(result: Iterator[tuple[str, str]]) -> None:
    for target, checksum in result:
        print(f"{target}:{checksum}")


def main() -> None:
    parser: ArgumentParser = _create_argument_parser()
    args: Namespace = parser.parse_args()

    result: Iterator[tuple[str, str]] = generate(args.targets)
    print_result(result)


if __name__ == "__main__":
    main()
