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


# def test_make_family_dir_if_necessary_actually_makes_the_directory(tmp_path, no_odd_config):
#     MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, 'America/Denver')
#     todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}"), MockDateTime.now())
#     no_odd_config.family_dir = tmp_path
#
#     make_family_files(tmp_path)
#
#     make_family_dir_if_necessary(no_odd_config, todays_family_dir)
#     assert os.path.exists(todays_family_dir)
#
#
# def test_make_family_dir_if_necessary_copies_all_the_files(tmp_path, no_odd_config):
#     MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, 'America/Denver')
#     todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}"), MockDateTime.now())
#     no_odd_config.family_dir = tmp_path
#
#     make_family_files(tmp_path)
#
#     make_family_dir_if_necessary(no_odd_config, todays_family_dir)
#     files = os.listdir(todays_family_dir)
#     assert (len(files) == 9)
#
#
# def test_get_families_from_dir_honors_regex(tmp_path, no_odd_config):
#     MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, 'America/Denver')
#     todays_family_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}"), MockDateTime.now())
#     no_odd_config.family_dir = tmp_path
#
#     make_family_files(tmp_path)
#
#     make_family_dir_if_necessary(no_odd_config, todays_family_dir)
#
#     families: [Family] = get_families_from_dir(family_dir=todays_family_dir, config=no_odd_config)
#     assert ([f.name for f in families] == ['f2', 'f4', 'f6', 'fa', 'fb'])
#

def make_family_files(tmp_path):
    # make family files
    for f in ('fa', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'fb'):
        with open(os.path.join(tmp_path, f), "w") as fp:
            fp.write('queue = "foo"')
