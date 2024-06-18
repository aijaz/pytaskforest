import datetime
import os

import pytz

from .config import Config
from .mockdatetime import MockDateTime, MockSleep
from .dirs import (
    copy_files_from_dir_to_dir,
    dated_dir,
    does_dir_exist,
    make_dir,
    text_files_in_dir,
)
from .family import Family


def main(config: Config):
    now: datetime.datetime = MockDateTime.now(tz=pytz.timezone(config.primary_tz))
    todays_family_dir = dated_dir(os.path.join(config.family_dir, "{YYYY}{MM}{DD}"), now)
    make_family_dir_if_necessary(config, todays_family_dir)
    families = get_families_from_dir(family_dir=todays_family_dir, config=config)
    todays_log_dir = dated_dir(os.path.join(config.log_dir, "{YYYY}{MM}{DD}"), now)
    make_dir_if_necessary(todays_log_dir)
    config.todays_log_dir = todays_log_dir
    config.todays_family_dir = todays_family_dir

    end_time = datetime.datetime(year=now.year,
                                 month=now.month,
                                 day=now.day,
                                 hour=config.end_time_hr,
                                 minute=config.end_time_min,
                                 tzinfo=pytz.timezone(config.primary_tz))
    run_main_loop_until_end(config, end_time, main_function, families=families)


def make_family_dir_if_necessary(config, todays_family_dir):
    if not does_dir_exist(todays_family_dir):
        make_dir(todays_family_dir)
        copy_files_from_dir_to_dir(config.family_dir, todays_family_dir)


def make_dir_if_necessary(the_dir):
    if not does_dir_exist(the_dir):
        make_dir(the_dir)


def get_families_from_dir(family_dir: str, config: Config) -> [Family]:
    files = text_files_in_dir(family_dir, config.ignore_regex)
    files.sort(key=lambda tup: tup[0])
    return [Family.parse(family_name=item[0], family_str=item[1], config=config) for item in files]


def run_main_loop_until_end(config: Config, end_time: datetime, function_to_run, families: [Family]):
    while True:
        now: datetime.datetime = MockDateTime.now(tz=pytz.timezone(config.primary_tz))
        if now >= end_time:
            break

        function_to_run(config, families)  # Assume this takes less than a minute to run
        now: datetime.datetime = MockDateTime.now(tz=pytz.timezone(config.primary_tz))
        MockSleep.sleep(60 - now.second)

    # TODO: Log here


def main_function(config: Config, families: [Family]):
    # Look at every family in today's family dir
    pass
