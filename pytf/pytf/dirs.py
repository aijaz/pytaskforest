import datetime
import os
import pathlib
import re
import shutil


def dated_dir(dir_name: str, timestamp:datetime.datetime) -> str:
    resolution_hash = { "YYYY": f"{timestamp.year}",
                        "MM":   f"{timestamp.month:02}",
                        "DD":   f"{timestamp.day:02}",
                        "hh":   f"{timestamp.hour:02}",
                        "mm":   f"{timestamp.month:02}",
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
            print(f"{ignore_regex=}, {file.name=}")
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


