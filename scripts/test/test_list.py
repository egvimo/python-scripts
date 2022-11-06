import os
import glob
import pytest
from scripts import list as ls


TEST_PATH = './out'
TEST_FILES = TEST_PATH + '/*.csv'


@pytest.fixture(autouse=True)
def prepare():
    if os.path.exists(TEST_PATH):
        files = glob.glob(TEST_FILES)
        for file in files:
            os.remove(file)


def test_list():
    ls.create_csv('/tmp', TEST_PATH)

    assert os.path.exists(TEST_PATH)
    assert len(glob.glob(TEST_FILES)) > 0
