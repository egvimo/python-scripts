#!/usr/bin/env python3

import argparse
import csv
import os
from datetime import datetime
from os import path
from pathlib import Path


def check_directory(directory_string):
    if not path.isdir(directory_string):
        raise argparse.ArgumentTypeError("invalid directory")
    return directory_string


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Generates a comma separated file containing information "
            "about files and folders of given directory"
        )
    )
    parser.add_argument(
        "-d", "--directory", type=check_directory, required=True, help="input directory"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="out", help="destination directory"
    )
    return parser.parse_args()


def append_record(data, file_path, files):
    for filename in files:
        filetype = "f"
        filesize = ""
        mod_time = ""

        file = path.join(file_path, filename)

        if path.islink(file):
            filetype = "l"
        elif path.isdir(file):
            filetype = "d"
            mod_time = datetime.fromtimestamp(path.getmtime(file)).strftime(
                "%Y-%m-%d-%H:%M"
            )
        else:
            stat = os.stat(file)
            filesize = stat.st_size
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d-%H:%M")
        data.append([file, filetype, filesize, mod_time])


def write_data(destination_dir, destination_file, data):
    Path(destination_dir).mkdir(parents=True, exist_ok=True)
    with open(
        path.join(destination_dir, destination_file), "w", encoding="utf8"
    ) as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        writer.writerows(data)


def create_csv(root_dir, destination_dir="out"):
    for subdir in next(os.walk(root_dir))[1]:
        data = [["file", "type", "size", "timestamp"]]
        for dirpath, dirnames, filenames in os.walk(path.join(root_dir, subdir)):
            append_record(data, dirpath, dirnames + filenames)
        write_data(destination_dir, f"{subdir}.csv", data)


if __name__ == "__main__":
    args = parse_arguments()
    create_csv(args.directory, args.output)
