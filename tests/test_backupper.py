import json
import os
from pathlib import Path
import shutil
import uuid
import pytest

from scripts.backupper import Backupper
from scripts.common import Config


TEST_PATH = './out'
TARGET_DIR = f"{TEST_PATH}/test"
TEST_ARCHIVE = f"{TEST_PATH}/test.7z"
PASSWORD = 'test'


@pytest.fixture(autouse=True)
def prepare():
    # pylint: disable=duplicate-code
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)
    Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        with open(f"{TARGET_DIR}/file{i}.txt", 'w', encoding='utf-8') as file:
            file.write(f"Random string in file {i} {uuid.uuid4()}")


def test_backup():
    with open(f"{TEST_PATH}/backupper.json", 'w', encoding='utf-8') as file:
        json.dump({'sources': [{'path': TARGET_DIR}]}, file)

    config = Config(f"{TEST_PATH}/backupper.json")

    backupper = Backupper()
    backupper._config = config  # pylint: disable=protected-access

    result = dict(backupper.run(destination=TEST_PATH, password=PASSWORD))

    assert os.path.isfile(TEST_ARCHIVE)
    assert result[os.path.normpath(TEST_ARCHIVE)]

    with open(f"{TEST_PATH}/backupper.json", 'r', encoding='utf-8') as file:
        source = json.load(file)['sources'][0]
        assert len(source['checksum']) == 40
