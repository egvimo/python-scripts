#!/usr/bin/env python3

from argparse import ArgumentParser
import json
import os
import shlex
import subprocess


_HOME = os.path.expanduser('~')
_XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME') or \
    os.path.join(_HOME, '.config')
_CONFIG_PATH = os.path.join(_XDG_CONFIG_HOME, 'archiver', 'config.json')


def _create_argument_parser() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        description='Creates or tests 7zip archives by calling 7z binary')

    subparsers = parser.add_subparsers(
        help='action to perform', dest='action')

    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-p', '--password', type=str, help='password')

    a_parser = subparsers.add_parser(
        'a', parents=[parent_parser], help='create archive')
    t_parser = subparsers.add_parser(
        't', parents=[parent_parser], help='test archive')

    a_parser.add_argument('targets', nargs='+',
                          help='directories to archive')

    t_parser.add_argument('archives', nargs='+', help='archives to test')

    return parser


def _read_config(config_path: str) -> str | None:
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as config:
            return json.load(config)
    return None


def _get_password(password: str = None) -> str:
    if password:
        return password
    config = _read_config(_CONFIG_PATH)
    if config and 'defaultPassword' in config and config['defaultPassword'].strip():
        return config['defaultPassword']
    raise ValueError("Password has to be provided")


def create_archive(*targets, password: str = None) -> None:
    password: str = _get_password(password)
    for target in targets:
        basename = os.path.basename(target)
        command = shlex.split(
            f"7z a -t7z -m0=LZMA2 -mhe=on -mmt=on -mx=9 -mfb=96 -md=128m "
            f"'-p{password}' {basename}.7z {target}"
        )
        subprocess.run(command, check=True)


def test_archive(*archives, password: str = None) -> None:
    password: str = _get_password(password)
    for archive in archives:
        command = shlex.split(f"7z t '-p{password}' {archive}")
        subprocess.run(command, check=True)


def main() -> None:
    parser = _create_argument_parser()
    args = parser.parse_args()

    if args.action == 'a':
        create_archive(args.targets, args.password)
    elif args.action == 't':
        test_archive(args.archives, args.password)


if __name__ == '__main__':
    main()
