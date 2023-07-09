#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError, Namespace
import os
import shlex
import subprocess
import sys
from typing import Iterator

import common


class Archiver:

    def __init__(self) -> None:
        self._config = common.Config('archiver.json')

    def create_archives(
        self,
        inputs: Iterator[str],
        destination: str | None = None,
        password: str | None = None,
        verbose: bool | None = None
    ) -> Iterator[tuple[str, bool]]:
        password: str = self._get_password(password)
        verbose: bool = self._get_verbose(verbose)

        for i in inputs:
            normpath = os.path.normpath(i)
            basename = os.path.basename(normpath)
            if destination:
                archive = os.path.normpath(
                    f"{os.path.join(destination, basename)}.7z")
            else:
                archive = f"{basename}.7z"
            command = shlex.split(
                f"7z a -t7z -m0=LZMA2 -mhe=on -mmt=on -mx=9 -mfb=96 -md=128m "
                f"'-p{password}' '{archive}' '{normpath}'"
            )
            completed_process = subprocess.run(
                command, check=False, capture_output=True)

            try:
                completed_process.check_returncode()
            except subprocess.CalledProcessError as ex:
                print(completed_process.stderr.decode(), file=sys.stderr)
                raise ex

            stdout = completed_process.stdout.decode()

            if verbose:
                print(stdout)

            yield archive, 'Everything is Ok' in stdout

    def test_archives(
        self,
        archives: Iterator[str],
        password: str | None = None,
        verbose: bool | None = None
    ) -> Iterator[tuple[str, bool]]:
        password: str = self._get_password(password)
        verbose: bool = self._get_verbose(verbose)

        for archive in archives:
            normpath = os.path.normpath(archive)
            command = shlex.split(f"7z t '-p{password}' '{normpath}'")
            completed_process = subprocess.run(
                command, check=False, capture_output=True)

            try:
                completed_process.check_returncode()
            except subprocess.CalledProcessError as ex:
                print(completed_process.stderr.decode(), file=sys.stderr)
                raise ex

            stdout = completed_process.stdout.decode()

            if verbose:
                print(stdout)

            yield normpath, 'Everything is Ok' in stdout

    def _get_password(self, password: str | None = None) -> str:
        if password and password.strip():
            return password
        password: str = self._config.get_value('defaultPassword')
        if password:
            return password
        raise ValueError("Password has to be provided")

    def _get_verbose(self, verbose: bool | None = None) -> bool:
        if verbose is not None:
            return verbose
        verbose: bool = self._config.get_value('verbose')
        return verbose if verbose else False


def _check_directory(directory_string):
    if not os.path.isdir(directory_string):
        raise ArgumentTypeError('invalid target directory')
    return directory_string


def _create_argument_parser() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        description='Creates or tests 7zip archives by calling 7z binary')

    subparsers = parser.add_subparsers(help='action to perform', dest='action')

    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument('-p', '--password', type=str, help='password')
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='verbose')

    a_parser = subparsers.add_parser(
        'a', parents=[parent_parser], help='create archive')
    t_parser = subparsers.add_parser(
        't', parents=[parent_parser], help='test archive')

    a_parser.add_argument('-d', '--destination',
                          type=_check_directory, help='destination directory')
    a_parser.add_argument('inputs', nargs='+', help='directories to archive')

    t_parser.add_argument('archives', nargs='+', help='archives to test')

    return parser


def print_result(result: Iterator[tuple[str, bool]]) -> None:
    for archive, success in result:
        print(f"{'✅' if success else '❌'} {archive}")


def main() -> None:
    parser: ArgumentParser = _create_argument_parser()
    args: Namespace = parser.parse_args()
    archiver: Archiver = Archiver()

    if args.action == 'a':
        result = archiver.create_archives(
            args.inputs, args.destination, args.password, args.verbose)
        print_result(result)
    elif args.action == 't':
        result = archiver.test_archives(
            args.archives, args.password, args.verbose)
        print_result(result)


if __name__ == '__main__':
    main()
