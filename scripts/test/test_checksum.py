import os
from pathlib import Path
import shutil
import uuid
import pytest
from scripts import checksum


TEST_PATH = './out'
TARGET_DIR = f"{TEST_PATH}/test"
NORM_TARGET_DIR = os.path.normpath(TARGET_DIR)


@pytest.fixture(autouse=True)
def prepare():
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)
    Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        with open(f"{TARGET_DIR}/file{i}.txt", 'w', encoding='utf-8') as file:
            file.write(f"Random string in file {i} {uuid.uuid4()}")


def test_checksum():
    result = checksum.generate_checksum([TARGET_DIR])

    assert result[NORM_TARGET_DIR]
    assert len(result[NORM_TARGET_DIR]) == 40


def test_checksum_changed():
    checksum1 = checksum.generate_checksum([TARGET_DIR])[NORM_TARGET_DIR]

    with open(f"{TARGET_DIR}/file1.txt", 'w', encoding='utf-8') as file:
        file.write(f"New random string in file {uuid.uuid4()}")

    checksum2 = checksum.generate_checksum([TARGET_DIR])[NORM_TARGET_DIR]

    assert checksum1 != checksum2
