import json
import os
from pathlib import Path
import shutil
from subprocess import CalledProcessError
import uuid
import pytest

from scripts.archiver import Archiver
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


def test_archiving():
    archiver = Archiver()
    result = dict(archiver.create_archives([TARGET_DIR], TEST_PATH, PASSWORD))

    assert os.path.isfile(TEST_ARCHIVE)
    assert result[os.path.normpath(TEST_ARCHIVE)]


def test_archiving_with_config():
    with open(f"{TEST_PATH}/archiver.json", 'w', encoding='utf-8') as file:
        json.dump({'defaultPassword': 'test'}, file)

    config = Config(f"{TEST_PATH}/archiver.json")

    archiver = Archiver()
    archiver._config = config  # pylint: disable=protected-access

    result = dict(archiver.create_archives([TARGET_DIR], TEST_PATH))

    assert os.path.isfile(TEST_ARCHIVE)
    assert result[os.path.normpath(TEST_ARCHIVE)]


def test_archiving_without_destination():
    archiver = Archiver()
    result = dict(archiver.create_archives([TARGET_DIR], password=PASSWORD))

    assert os.path.isfile('test.7z')
    assert result[os.path.normpath('test.7z')]
    os.remove('test.7z')


def test_fail_archiving_without_password():
    archiver = Archiver()
    with pytest.raises(ValueError, match='Password has to be provided'):
        next(archiver.create_archives([TARGET_DIR]))


def test_fail_archiving_with_empty_password():
    archiver = Archiver()
    with pytest.raises(ValueError, match='Password has to be provided'):
        next(archiver.create_archives([TARGET_DIR], password=' '))


def test_testing():
    archiver = Archiver()
    next(archiver.create_archives([TARGET_DIR], TEST_PATH, PASSWORD))

    result = dict(archiver.test_archives([TEST_ARCHIVE], PASSWORD))
    assert result[os.path.normpath(TEST_ARCHIVE)]


def test_fail_testing_without_password():
    archiver = Archiver()
    next(archiver.create_archives([TARGET_DIR], TEST_PATH, PASSWORD))

    with pytest.raises(ValueError, match='Password has to be provided'):
        next(archiver.test_archives([TEST_ARCHIVE]))


def test_fail_testing_with_empty_password():
    archiver = Archiver()
    next(archiver.create_archives([TARGET_DIR], TEST_PATH, PASSWORD))

    with pytest.raises(ValueError, match='Password has to be provided'):
        next(archiver.test_archives([TEST_ARCHIVE], ' '))


def test_fail_testing_with_wrong_password(capfd):
    archiver = Archiver()
    next(archiver.create_archives([TARGET_DIR], TEST_PATH, PASSWORD))

    with pytest.raises(CalledProcessError):
        next(archiver.test_archives([TEST_ARCHIVE], 'wrong'))

    _, err = capfd.readouterr()
    assert 'Wrong password?' in err
