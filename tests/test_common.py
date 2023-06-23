import json
import os
from pathlib import Path
import shutil
import pytest

from scripts.common import Config


TEST_PATH = './out'
TARGET_DIR = f"{TEST_PATH}/test"
TEST_ARCHIVE = f"{TEST_PATH}/test.7z"
PASSWORD = 'test'


@pytest.fixture(autouse=True)
def prepare():
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)
    Path(TEST_PATH).mkdir(parents=True, exist_ok=True)


def test_config():
    with open(f"{TEST_PATH}/test.json", 'w', encoding='utf-8') as config:
        json.dump({'testKey': 'testValue'}, config)

    config = Config('test.json')
    config._CONFIG_PATH = os.path.join(  # pylint: disable=protected-access
        os.getcwd(), TEST_PATH)

    value = config.get_value('testKey')

    assert value == 'testValue'
