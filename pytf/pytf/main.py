import datetime
from time import sleep

import pytz

from .config import Config
from mockdatetime import MockDateTime, MockSleep


def main(config:Config):
    now:datetime.datetime = MockDateTime.now(tz=pytz.timezone(config.primary_tz))
    end_time = datetime.datetime(year=now.year,
                                 month=now.month,
                                 day=now.day,
                                 hour=config.end_time_hr,
                                 minute=config.end_time_min,
                                 tzinfo=pytz.timezone(config.primary_tz))
    run_main_loop_until_end(config, end_time, main_function)


def run_main_loop_until_end(config: Config, end_time: datetime, function_to_run):
    while True:
        now: datetime.datetime = MockDateTime.now(tz=pytz.timezone(config.primary_tz))
        if now >= end_time:
            break

        function_to_run(config)  # Assume this takes less than a minute to run
        now: datetime.datetime = MockDateTime.now(tz=pytz.timezone(config.primary_tz))
        MockSleep.sleep(60 - now.second)

    # TODO: Log here


def main_function(config: Config):
    pass