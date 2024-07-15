import os
import pytest

from pytf.mockdatetime import MockDateTime
from pytf.dirs import dated_dir
# from pytf.main import make_family_dir_if_necessary, get_families_from_dir
from pytf.config import Config
from pytf.family import Family


@pytest.fixture
def no_odd_config():
    return Config.from_str("""
    calendars.daily = [
      "*/*/*"
    ]
    calendars.mondays = [
      "every Monday */*"
    ]
    ignore_regex = [
      ".*[13579]$"
    ]
    """)


def test_todays_family_dir(tmp_path, no_odd_config):
    MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, 'America/Denver')
    todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}"), MockDateTime.now())
    no_odd_config.family_dir = tmp_path
    assert (todays_family_dir == os.path.join(tmp_path, "20240603"))


def test_dated_dir_does_not_create_dir(tmp_path, no_odd_config):
    MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, 'America/Denver')
    todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}"), MockDateTime.now())
    no_odd_config.family_dir = tmp_path
    assert not os.path.exists(todays_family_dir)


