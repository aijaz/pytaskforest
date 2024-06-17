import os
import pytest
import pytz

from pytf.pytf.mockdatetime import MockDateTime
from pytf.pytf.dirs import dated_dir
from pytf.pytf.main import make_family_dir_if_necessary
from pytf.pytf.config import Config


@pytest.fixture
def no_odd_config():
    return Config.from_str("""
    calendars.daily = [
      "*/*/*"
    ]
    calendars.mondays = [
      "every Monday */*"
    ]
    ignore_regexes = [
      ".*[13579]$"
    ]
    """)

def test_make_family_dir_if_necessary(tmp_path, no_odd_config):
    MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, pytz.timezone('America/Denver'))
    todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}-{MM}-{DD}"), MockDateTime.now())
    no_odd_config.family_dir = tmp_path
    assert(todays_family_dir == os.path.join(tmp_path, "2024-06-03"))
    assert not os.path.exists(todays_family_dir)

    # make family files
    for f in ('fa', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'fb'):
        with open(os.path.join(tmp_path, f), "w") as fp:
            fp.write('queue: "foo"')

    files = os.listdir(tmp_path)
    assert(len(files) == 9)

    make_family_dir_if_necessary(no_odd_config, todays_family_dir)
    assert os.path.exists(todays_family_dir)
    files = os.listdir(todays_family_dir)
    assert(len(files) == 9)

