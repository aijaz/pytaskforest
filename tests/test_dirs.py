import os

import pathlib
import pytest

from pytf.dirs import (
    copy_files_from_dir_to_dir,
    dated_dir,
    dated_subdir,
    dated_subdir_primary_today,
    does_dir_exist,
    list_of_files_in_dir,
    todays_log_dir,
    todays_family_dir,
)
from pytf.config import Config
from pytf.mockdatetime import MockDateTime


@pytest.fixture
def denver_config():
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
    primary_tz = "America/Denver"
    log_dir = "/a/l"
    family_dir = "/a/f"
    """)


def _make_files_in_dir1(p):
    dir1 = os.path.join(p, 'dir1')
    dir2 = os.path.join(p, 'dir2')
    os.makedirs(dir1)
    os.makedirs(dir2)

    with open(os.path.join(dir1, "f1"), "w") as f:
        f.write("This is line 1 of f1\n")
        f.write("This is line 2 of f1\n")

    with open(os.path.join(dir1, "f2"), "w") as f:
        f.write("This is line 1 of f2\n")
        f.write("This is line 2 of f2\n")

    return dir1, dir2


def test_copy_files_from_dir_to_dir_len(tmp_path):
    dir1, dir2 = _make_files_in_dir1(tmp_path)

    copy_files_from_dir_to_dir(dir1, dir2)

    dir1_files = os.listdir(dir1)
    dir2_files = os.listdir(dir2)
    assert (len(dir1_files) == len(dir2_files))


def test_copy_files_from_dir_to_dir_contents(tmp_path):
    dir1, dir2 = _make_files_in_dir1(tmp_path)

    copy_files_from_dir_to_dir(dir1, dir2)

    assert (pathlib.Path(os.path.join(dir1, "f1")).read_text() == pathlib.Path(os.path.join(dir2, "f1")).read_text())
    assert (pathlib.Path(os.path.join(dir1, "f2")).read_text() == pathlib.Path(os.path.join(dir2, "f2")).read_text())


def test_does_dir_exist(tmp_path):
    assert (does_dir_exist(str(tmp_path)))


def test_dated_dir(tmp_path):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'America/Denver')
    the_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}{hh}{mm}{ss}"), MockDateTime.now('America/Denver'))
    assert (the_dir == os.path.join(tmp_path, "20240601010203"))


def test_dated_dir_differnt_timezone(tmp_path):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'America/Denver')
    the_dir = dated_dir(os.path.join(tmp_path, "{YYYY}{MM}{DD}{hh}{mm}{ss}"), MockDateTime.now('America/Chicago'))
    assert (the_dir != os.path.join(tmp_path, "20240601010203"))


def test_dated_subdir(tmp_path):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'America/Denver')
    the_dir = dated_subdir(str(tmp_path), MockDateTime.now('America/Denver'))
    assert (the_dir == os.path.join(tmp_path, "20240601"))


def test_dated_subdir_primary_today(tmp_path, denver_config):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'America/Denver')
    the_dir = dated_subdir_primary_today(str(tmp_path), config=denver_config)
    MockDateTime.set_mock(2024, 6, 1, 2, 4, 59, 'America/Denver')
    assert (the_dir == os.path.join(tmp_path, "20240601"))


def test_dated_subdir_primary_today_different_time_zone(tmp_path, denver_config):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'UTC')
    the_dir = dated_subdir_primary_today(str(tmp_path), config=denver_config)
    MockDateTime.set_mock(2024, 6, 1, 2, 4, 59, 'UTC')
    assert (the_dir == os.path.join(tmp_path, "20240531"))


def test_todays_log_dir(denver_config):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'America/Denver')
    the_dir = todays_log_dir(denver_config)
    assert (the_dir == os.path.join("/a/l/", "20240601"))


def test_todays_family_dir(denver_config):
    MockDateTime.set_mock(2024, 6, 1, 1, 2, 3, 'America/Denver')
    the_dir = todays_family_dir(denver_config)
    assert (the_dir == os.path.join("/a/f/", "20240601"))


def _create_9_files(p):
    with open(os.path.join(p, 'a'), "w") as f:
        f.write('a')
    with open(os.path.join(p, 's'), "w") as f:
        f.write('s')
    with open(os.path.join(p, 'd'), "w") as f:
        f.write('d')
    with open(os.path.join(p, 'f'), "w") as f:
        f.write('f')
    with open(os.path.join(p, 'g'), "w") as f:
        f.write('g')
    with open(os.path.join(p, 'l'), "w") as f:
        f.write('l')
    with open(os.path.join(p, 'k'), "w") as f:
        f.write('k')
    with open(os.path.join(p, 'j'), "w") as f:
        f.write('j')
    with open(os.path.join(p, 'h'), "w") as f:
        f.write('h')


def test_list_of_files_in_dir_len(tmp_path):
    _create_9_files(tmp_path)
    files = list_of_files_in_dir(str(tmp_path))
    assert len(files) == 9


def test_list_of_files_in_dir_sort_order(tmp_path):
    _create_9_files(tmp_path)
    files = list_of_files_in_dir(str(tmp_path))
    assert (files == sorted(files))