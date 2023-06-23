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
    result = archiver.create_archive(
        [TARGET_DIR], destination=TEST_PATH, password=PASSWORD)

    assert os.path.isfile(TEST_ARCHIVE)
    assert result[os.path.normpath(TEST_ARCHIVE)]


def test_archiving_with_config():
    with open(f"{TEST_PATH}/archiver.json", 'w', encoding='utf-8') as config:
        json.dump({'defaultPassword': 'test'}, config)

    config = Config('archiver.json')
    config._CONFIG_PATH = os.path.join(  # pylint: disable=protected-access
        os.getcwd(), TEST_PATH)

    archiver = Archiver()
    archiver._config = config  # pylint: disable=protected-access

    result = archiver.create_archive([TARGET_DIR], destination=TEST_PATH)

    assert os.path.isfile(TEST_ARCHIVE)
    assert result[os.path.normpath(TEST_ARCHIVE)]


def test_archiving_without_destination():
    archiver = Archiver()
    result = archiver.create_archive([TARGET_DIR], password=PASSWORD)

    assert os.path.isfile('test.7z')
    assert result[os.path.normpath('test.7z')]
    os.remove('test.7z')


def test_fail_archiving_without_password():
    archiver = Archiver()
    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.create_archive([TARGET_DIR])


def test_fail_archiving_with_empty_password():
    archiver = Archiver()
    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.create_archive([TARGET_DIR], password=' ')


def test_testing():
    archiver = Archiver()
    archiver.create_archive(
        [TARGET_DIR], destination=TEST_PATH, password=PASSWORD)

    result = archiver.test_archive([TEST_ARCHIVE], password=PASSWORD)
    assert result[os.path.normpath(TEST_ARCHIVE)]


def test_fail_testing_without_password():
    archiver = Archiver()
    archiver.create_archive(
        [TARGET_DIR], destination=TEST_PATH, password=PASSWORD)

    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.test_archive([TEST_ARCHIVE])


def test_fail_testing_with_empty_password():
    archiver = Archiver()
    archiver.create_archive(
        [TARGET_DIR], destination=TEST_PATH, password=PASSWORD)

    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.test_archive([TEST_ARCHIVE], ' ')


def test_fail_testing_with_wrong_password(capfd):
    archiver = Archiver()
    archiver.create_archive(
        [TARGET_DIR], destination=TEST_PATH, password=PASSWORD)

    with pytest.raises(CalledProcessError):
        archiver.test_archive([TEST_ARCHIVE], 'wrong')

    _, err = capfd.readouterr()
    assert 'Wrong password?' in err
