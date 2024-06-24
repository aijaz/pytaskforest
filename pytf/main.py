import datetime
import logging
import os

import pytz

from .config import Config
from .mockdatetime import MockDateTime, MockSleep
from .runner import prepare_required_dirs, run_shell_script
from .pytf_worker import run_task
from .status import status_and_families


def main(config: Config):
    logger = logging.getLogger('pytf_logger')

    now = prepare_required_dirs(config)

    logger.info("HERE")

    end_time = pytz.timezone(config.primary_tz).localize(datetime.datetime(year=now.year,
                                                                           month=now.month,
                                                                           day=now.day,
                                                                           hour=config.end_time_hr,
                                                                           minute=config.end_time_min))
    logger.info(f"{end_time=}")
    run_main_loop_until_end(config, end_time, main_function)


def run_main_loop_until_end(config: Config, end_time: datetime, function_to_run):
    logger = logging.getLogger('pytf_logger')
    sleep_time = 10
    while True:
        # primary_tz is used for the start and end time of the main loop
        now: datetime.datetime = MockDateTime.now(config.primary_tz)
        if now >= end_time:
            break

        function_to_run(config)  # Assume this takes less than a minute to run
        now: datetime.datetime = MockDateTime.now(tz=config.primary_tz)
        sleep_time_left = sleep_time - (now.second % sleep_time)
        logger.debug(f"Sleeping for {sleep_time_left}")
        MockSleep.sleep(sleep_time_left)


def main_function(config: Config):
    logger = logging.getLogger('pytf_logger')
    status, families = status_and_families(config)
    ready_jobs = [j for j in status['status']['flat_list'] if j['status'] == 'Ready']

    for job in ready_jobs:
        job_log_file = os.path.join(config.todays_log_dir, f"{job['family_name']}.{job['job_name']}.log")
        run_logger = logging.getLogger('run_logger')
        run_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(filename=job_log_file)
        handler.setFormatter(logging.Formatter("%(asctime)s -> %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"))
        handler.setLevel(logging.DEBUG)
        for old_handler in run_logger.handlers:
            run_logger.removeHandler(old_handler)
        run_logger.addHandler(handler)
        run_logger.propagate = False

        if config.run_local:
            logger.info(f"Gonna run job {job['family_name']}::{job['job_name']} locally")
            run_logger.info(f"Run Logger: Gonna run job {job['family_name']}::{job['job_name']} locally")
            script_path = os.path.join(config.job_dir, job['job_name'])
            now = MockDateTime.now(config.primary_tz)
            start_small = now.strftime("%Y%m%d%H%M%S")
            start_pretty = MockDateTime.now().astimezone(pytz.timezone(job['tz'])).strftime("%Y/%m/%d %H:%M:%S")

            info_path = os.path.join(config.todays_log_dir,
                                     f"{job['family_name']}.{job['job_name']}.x.x.{start_small}.info")
            with open(info_path, "w") as f:
                f.write(f'family_name = "{job['family_name']}"\n')
                f.write(f'job_name = "{job['job_name']}"\n')
                f.write(f'queue_name = "{job['queue_name']}"\n')
                f.write(f'tz = "{job['tz']}"\n')
                f.write(f'worker_name = "???"\n')
                f.write(f'start_time = "{start_pretty}"\n')
            err = run_shell_script(script_path)
            with open(info_path, "a") as f:
                f.write(f'error_code = {err}')
        else:
            logger.info(f"Queuing job {job['family_name']}::{job['job_name']} on queue: {job['queue_name']}")
            run_task.delay(config.todays_log_dir,
                           config.job_dir,
                           config.primary_tz,
                           job['family_name'],
                           job['job_name'],
                           job['tz'],
                           job['queue_name'],
                           job_log_file)
