#!/usr/bin/env python3

import json
import re
import subprocess
from pathlib import Path

BITRATE = "48k"


def clean_name(name: str) -> str:
    name = name or "Chapter"
    # Only safe characters
    name = re.sub(r"[^a-zA-Z0-9 _-]+", "", name)
    return name.strip()


def run_ffprobe(file_path: Path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_chapters",
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def encode_chapter(input_file: Path, out_file: Path, start: float, duration: float):
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-ss", str(start),
        "-i", str(input_file),
        "-t", str(duration),

        # Only audio stream
        "-map", "0:a:0",
        "-vn",

        "-c:a", "libopus",
        "-b:a", BITRATE,
        "-vbr", "on",
        "-compression_level", "10",

        # No broken metadata
        "-map_metadata", "-1",

        str(out_file)
    ]

    subprocess.run(cmd, check=True)


def process_file(file_path: Path):
    print(f"\n==> {file_path.name}")

    data = run_ffprobe(file_path)
    chapters = data.get("chapters", [])

    if not chapters:
        print("   ⚠ No chapters found – skipped")
        return

    out_dir = file_path.with_suffix("")
    out_dir.mkdir(exist_ok=True)

    for i, ch in enumerate(chapters, start=1):
        start = float(ch["start_time"])
        end = float(ch["end_time"])
        duration = end - start

        title = ch.get("tags", {}).get("title", f"Chapter {i}")
        title = clean_name(title)

        out_file = out_dir / f"{i:03d}_{title}.opus"

        print(f"   -> {out_file.name}")
        encode_chapter(file_path, out_file, start, duration)


def main():
    files = sorted(Path(".").glob("*.m4b"))

    if not files:
        print("No M4B files found.")
        return

    for f in files:
        try:
            process_file(f)
        except subprocess.CalledProcessError as e:
            print(f"Error with {f.name}: {e}")


if __name__ == "__main__":
    main()
