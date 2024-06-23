import datetime

import pytz

from .config import Config
from .mockdatetime import MockDateTime, MockSleep
from .runner import prepare_required_dirs, run_shell_script
from .status import status_and_families


def main(config: Config):
    now = prepare_required_dirs(config)

    end_time = pytz.timezone(config.primary_tz).localize(datetime.datetime(year=now.year,
                                                                           month=now.month,
                                                                           day=now.day,
                                                                           hour=config.end_time_hr,
                                                                           minute=config.end_time_min))
    run_main_loop_until_end(config, end_time, main_function)


def run_main_loop_until_end(config: Config, end_time: datetime, function_to_run):
    sleep_time = 10
    while True:
        # primary_tz is used for the start and end time of the main loop
        now: datetime.datetime = MockDateTime.now(config.primary_tz)
        if now >= end_time:
            break

        function_to_run(config)  # Assume this takes less than a minute to run
        now: datetime.datetime = MockDateTime.now(tz=config.primary_tz)
        sleep_time_left = sleep_time - (now.second % sleep_time)
        print(f"Sleeping for {sleep_time_left}")
        MockSleep.sleep(sleep_time_left)

    # TODO: Log here


def main_function(config: Config):
    status, families = status_and_families(config)
    ready_jobs = [j for j in status['status']['flat_list'] if j['status'] == 'Ready']
    for job in ready_jobs:
        if config.run_local:
            print(f"Gonna run job {job['family_name']}::{job['job_name']} locally")
        else:
            print(f"Gonna run job {job['family_name']}::{job['job_name']} remotely")
