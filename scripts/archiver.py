#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
import json
import os
import shlex
import subprocess
import sys


_HOME = os.path.expanduser('~')
_XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME') or \
    os.path.join(_HOME, '.config')
_CONFIG_PATH = os.path.join(_XDG_CONFIG_HOME, 'scripts', 'archiver.json')


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
    parent_parser.add_argument('-v', '--verbose', type=str, help='verbose')

    a_parser = subparsers.add_parser(
        'a', parents=[parent_parser], help='create archive')
    t_parser = subparsers.add_parser(
        't', parents=[parent_parser], help='test archive')

    a_parser.add_argument('-d', '--destination',
                          type=_check_directory, help='destination directory')
    a_parser.add_argument('inputs', nargs='+', help='directories to archive')

    t_parser.add_argument('archives', nargs='+', help='archives to test')

    return parser


def _read_config(config_path: str) -> str | None:
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as config:
            return json.load(config)
    return None


def _get_password(password: str = None) -> str:
    if password and password.strip():
        return password
    config = _read_config(_CONFIG_PATH)
    if config and 'defaultPassword' in config and config['defaultPassword'].strip():
        return config['defaultPassword']
    raise ValueError("Password has to be provided")


def _get_verbose(verbose: bool = None) -> bool:
    if verbose is not None:
        return verbose
    config = _read_config(_CONFIG_PATH)
    if config and 'verbose' in config and config['verbose'].strip():
        return config['verbose']
    return False


def create_archive(
    inputs: list[str],
    destination: str = None,
    password: str = None,
    verbose: bool = None
) -> dict[str, bool]:
    password: str = _get_password(password)
    verbose: bool = _get_verbose(verbose)

    result: dict[str, bool] = {}
    for i in inputs:
        normpath = os.path.normpath(i)
        basename = os.path.basename(normpath)
        if destination:
            archive = os.path.normpath(f"{os.path.join(destination, basename)}.7z")
        else:
            archive = f"{basename}.7z"
        command = shlex.split(
            f"7z a -t7z -m0=LZMA2 -mhe=on -mmt=on -mx=9 -mfb=96 -md=128m "
            f"'-p{password}' {archive} {normpath}"
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

        result[archive] = 'Everything is Ok' in stdout

    return result


def test_archive(
    archives: list[str],
    password: str = None,
    verbose: bool = None
) -> dict[str, bool]:
    password: str = _get_password(password)
    verbose: bool = _get_verbose(verbose)

    result: dict[str, bool] = {}
    for archive in archives:
        normpath = os.path.normpath(archive)
        command = shlex.split(f"7z t '-p{password}' {normpath}")
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

        result[normpath] = 'Everything is Ok' in stdout

    return result


def print_result(result: dict[str, bool]) -> None:
    for archive, success in result.items():
        print(f"{'✅' if success else '❌'} {archive}")


def main() -> None:
    parser = _create_argument_parser()
    args = parser.parse_args()

    result: dict[str, bool]
    if args.action == 'a':
        result = create_archive(args.inputs, args.destination,
                                args.password, args.verbose)
    elif args.action == 't':
        result = test_archive(args.archives, args.password, args.verbose)
    print_result(result)


if __name__ == '__main__':
    main()
