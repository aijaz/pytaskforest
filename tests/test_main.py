import os
import pytest
import pytz

from pytf.mockdatetime import MockDateTime
from pytf.dirs import dated_dir
from pytf.main import make_family_dir_if_necessary, get_families_from_dir
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


def test_make_family_dir_if_necessary(tmp_path, no_odd_config):
    MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, 'America/Denver')
    todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}"), MockDateTime.now())
    no_odd_config.family_dir = tmp_path
    assert(todays_family_dir == os.path.join(tmp_path, "20240603"))
    assert not os.path.exists(todays_family_dir)

    # make family files
    for f in ('fa', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'fb'):
        with open(os.path.join(tmp_path, f), "w") as fp:
            fp.write('queue = "foo"')

    files = os.listdir(tmp_path)
    assert(len(files) == 9)

    make_family_dir_if_necessary(no_odd_config, todays_family_dir)
    assert os.path.exists(todays_family_dir)
    files = os.listdir(todays_family_dir)
    assert(len(files) == 9)

    families: [Family] = get_families_from_dir(family_dir=todays_family_dir, config=no_odd_config)
    assert(len(families) == 5)
    assert(families[0].name == 'f2')
    assert(families[1].name == 'f4')
    assert(families[2].name == 'f6')
    assert(families[3].name == 'fa')
    assert(families[4].name == 'fb')