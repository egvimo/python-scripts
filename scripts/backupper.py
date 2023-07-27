#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError, Namespace
import os
from typing import Iterator

from common import Config, Logger
from archiver import Archiver
import checksum


logger = Logger()


class Backupper:  # pylint: disable=too-few-public-methods
    def __init__(self, verbose: bool = False) -> None:
        self._config = Config("backupper.json")
        self._archiver = Archiver()
        self._verbose = verbose
        if verbose:
            logger.verbose()

    def run(
        self, destination: str | None = None, password: str | None = None
    ) -> Iterator[tuple[str, bool]]:
        config = self._config.get_config()
        sources = config["sources"]

        if not sources:
            logger.warning("No sources defined")
            return iter(())

        paths = [s["path"] for s in sources]
        checksums = checksum.generate(paths)

        archives: list[str] = []
        for path, digest in checksums:
            for source in sources:
                if not os.path.samefile(path, source["path"]):
                    continue
                if digest != source.get("checksum", None):
                    source["checksum"] = digest
                    archives.append(path)

        self._config.set_config(config)

        return self._archiver.create_archives(
            archives, destination=destination, password=password, verbose=self._verbose
        )


def _check_directory(directory_string):
    if not os.path.isdir(directory_string):
        raise ArgumentTypeError("invalid destination directory")
    return directory_string


def _create_argument_parser() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        description="Backups data by creating 7zip archives"
    )
    parser.add_argument("-p", "--password", type=str, help="password")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")
    parser.add_argument(
        "-d", "--destination", type=_check_directory, help="destination directory"
    )
    return parser


def main() -> None:
    parser: ArgumentParser = _create_argument_parser()
    args: Namespace = parser.parse_args()

    backupper = Backupper(args.verbose)
    backupper.run(args.destination, args.password)


if __name__ == "__main__":
    main()
