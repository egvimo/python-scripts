import os
import glob
import pytest

from scripts import enny_mo


EPISODE_BOUNDARY = 87

TEST_PATH = './out'
TEST_FILES = TEST_PATH + '/*.mp3'


@pytest.fixture(autouse=True)
def prepare():
    if os.path.exists(TEST_PATH):
        files = glob.glob(TEST_FILES)
        for file in files:
            os.remove(file)


@pytest.mark.skip(reason='Switched to podcast')
def test_episode_download():
    enny_mo.start_crawler(EPISODE_BOUNDARY)

    assert os.path.exists(TEST_PATH)
    assert len(glob.glob(TEST_FILES)) > 0
