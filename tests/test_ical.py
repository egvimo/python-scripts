import os
import pytest
from scripts import ical

DATA = {
    'Test': ['05.01.2021', '10.03.2021']
}

RESULT = ('BEGIN:VCALENDAR\n'
          'BEGIN:VEVENT\n'
          'SUMMARY:Test\n'
          'DTSTART;VALUE=DATE:20210105\n'
          'TRANSP:TRANSPARENT\n'
          'END:VEVENT\n'
          'BEGIN:VEVENT\n'
          'SUMMARY:Test\n'
          'DTSTART;VALUE=DATE:20210310\n'
          'TRANSP:TRANSPARENT\n'
          'END:VEVENT\n'
          'END:VCALENDAR')

TEST_PATH = './out/test.ics'


@pytest.fixture(autouse=True)
def prepare():
    if os.path.exists(TEST_PATH):
        os.remove(TEST_PATH)


def test_ical_creation():
    cal = ical.create_ical(DATA)

    assert cal.to_ical().decode('utf-8').replace('\r\n', '\n').strip() == RESULT


def test_ical_export():
    cal = ical.create_ical(DATA)
    ical.export_to_file(cal, filename='test.ics')

    assert os.path.exists(TEST_PATH)
    with open(TEST_PATH, 'r', encoding='utf-8') as file:
        assert file.read().strip() == RESULT
