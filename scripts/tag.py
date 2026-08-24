import re
from pathlib import Path

from mutagen import MutagenError
from mutagen.oggopus import OggOpus

files = sorted(Path("/path/to/files").glob("*.opus"))

current_book = None
chapter_counter = 0

for file in files:
    stem = file.stem

    # Match filenames like:
    # 11_002_Chapter 2_Some Chapter Title
    # 12_045_Chapter 45_Other Chapter Title
    #
    # but NOT:
    # 11_003_Chapter 3

    m = re.match(r"^\d+_\d+_Chapter \d+_(.+)$", stem)

    if m:
        current_book = m.group(1).strip()
        chapter_counter = 1
    else:
        chapter_counter += 1

    if not current_book:
        print(f"Skipping {file.name} (no chapter book yet)")
        continue

    title = f"{current_book} - {chapter_counter:02d}"

    try:
        audio = OggOpus(file)
        audio["TITLE"] = [title]
        audio.save()

        print(f"{file.name} -> {title}")

    except (MutagenError, OSError) as e:
        print(f"ERROR {file.name}: {e}")
