import json
import os
from pathlib import Path
import shutil
from subprocess import CalledProcessError
import uuid
import pytest
from scripts import archiver


TEST_PATH = './test'
TEST_ARCHIVE = './test.7z'
PASSWORD = 'test'


@pytest.fixture(autouse=True)
def prepare(monkeypatch):
    if os.path.exists('./out'):
        shutil.rmtree('./out')
    Path('./out/test').mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir('./out')
    for i in range(1, 4):
        with open(TEST_PATH + f"/file{i}.txt", 'w', encoding='utf-8') as file:
            file.write(f"Random string in file {i} {uuid.uuid4()}")


def test_archiving():
    archiver.create_archive(TEST_PATH, password=PASSWORD)

    assert os.path.isfile(TEST_ARCHIVE)


def test_archiving_with_config():
    Path('./archiver').mkdir(parents=True, exist_ok=True)
    with open('./archiver/config.json', 'w', encoding='utf-8') as config:
        json.dump({'defaultPassword': 'test'}, config)

    archiver._CONFIG_PATH = f"{os.getcwd()}/archiver/config.json"  # pylint: disable=protected-access

    archiver.create_archive(TEST_PATH)

    assert os.path.isfile(TEST_ARCHIVE)


def test_fail_archiving_without_password():
    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.create_archive(TEST_PATH)


def test_fail_archiving_with_empty_password():
    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.create_archive(TEST_PATH, ' ')


def test_testing():
    archiver.create_archive(TEST_PATH, password=PASSWORD)

    archiver.test_archive(TEST_ARCHIVE, password=PASSWORD)


def test_fail_testing_without_password():
    archiver.create_archive(TEST_PATH, password=PASSWORD)

    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.test_archive(TEST_ARCHIVE)


def test_fail_testing_with_empty_password():
    archiver.create_archive(TEST_PATH, password=PASSWORD)

    with pytest.raises(ValueError, match='Password has to be provided'):
        archiver.test_archive(TEST_ARCHIVE, ' ')


def test_fail_testing_with_wrong_password(capfd):
    archiver.create_archive(TEST_PATH, password=PASSWORD)

    with pytest.raises(CalledProcessError):
        archiver.test_archive(TEST_ARCHIVE, password='wrong')

    _, err = capfd.readouterr()
    assert 'Wrong password?' in err
