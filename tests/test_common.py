import json
import os
import shutil
from pathlib import Path

import pytest

from scripts.common import Config

TEST_PATH = "./out"
TARGET_DIR = f"{TEST_PATH}/scripts"
PASSWORD = "test"


@pytest.fixture(autouse=True)
def prepare():
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)
    Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)


def test_config():
    with open(f"{TEST_PATH}/test.json", "w", encoding="utf-8") as file:
        json.dump({"testKey": "testValue"}, file)

    config = Config(f"{TEST_PATH}/test.json")

    value = config.get_value("testKey")

    assert value == "testValue"


@pytest.mark.skip(reason="Static variables are initialized on import")
def test_config_with_config_home(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", TEST_PATH)

    with open(f"{TARGET_DIR}/test.json", "w", encoding="utf-8") as file:
        json.dump({"testKey": "testValue"}, file)

    config = Config("test.json")

    value = config.get_value("testKey")

    assert value == "testValue"
