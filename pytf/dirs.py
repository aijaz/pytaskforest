import datetime
import os
import pathlib
import re
import shutil

from .mockdatetime import MockDateTime
from .config import Config


def todays_family_dir(config: Config) -> str:
    return dated_subdir_primary_today(config.family_dir, config)


def todays_log_dir(config: Config) -> str:
    return dated_subdir_primary_today(config.log_dir, config)


def dated_subdir_primary_today(dir_name: str, config: Config) -> str:
    now = MockDateTime.now(tz=config.primary_tz)
    return dated_subdir(dir_name, now)


def dated_subdir(dir_name: str, timestamp: datetime.datetime) -> str:
    return dated_dir(os.path.join(dir_name, "{YYYY}{MM}{DD}"), timestamp)


def dated_dir(dir_name: str, timestamp:datetime.datetime) -> str:
    resolution_hash = { "YYYY": f"{timestamp.year}",
                        "MM":   f"{timestamp.month:02}",
                        "DD":   f"{timestamp.day:02}",
                        "hh":   f"{timestamp.hour:02}",
                        "mm":   f"{timestamp.minute:02}",
                        "ss":   f"{timestamp.second:02}",
                        }
    return dir_name.format(**resolution_hash)


def does_dir_exist(dir_name: str) -> bool:
    return os.path.exists(dir_name)


def make_dir(dir_name: str):
    os.makedirs(dir_name)


def text_files_in_dir(dir_name: str, ignore_regexes: [str]) -> [(str, str)]:
    dir_path = pathlib.Path(dir_name)
    files = [item for item in dir_path.iterdir() if item.is_file()]
    filtered = []
    for file in files:
        matched = False
        for ignore_regex in ignore_regexes:
            regex = re.compile(ignore_regex)
            if regex.match(file.name):
                matched = True
                break
        if not matched:
            filtered.append(file)

    return [(file.name, file.read_text()) for file in filtered]


def copy_files_from_dir_to_dir(src: str, dest: str):
    src_path = pathlib.Path(src)
    files = [item for item in src_path.iterdir() if item.is_file()]
    for file in files:
        shutil.copyfile(os.path.join(src, file.name), os.path.join(dest, file.name))


def make_dir_if_necessary(the_dir):
    if not does_dir_exist(the_dir):
        make_dir(the_dir)


def list_of_files_in_dir(dir_name: str) -> [str]:
    path = pathlib.Path(dir_name)
    files = [item.name for item in path.iterdir() if item.is_file()]
    files.sort()
    return files

