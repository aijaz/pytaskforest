import datetime
import logging
import os

import pytz

from .config import Config
from .mockdatetime import MockDateTime, MockSleep
from .runner import prepare_required_dirs, run_shell_script
from .pytf_worker import run_task
from .status import status_and_families_and_token_doc
from .pytftoken import PyTfToken
from .pytf_logging import setup_logging
import pytf.dirs as dirs


def setup_logging_and_tokens(config):
    setup_logging(config.log_dir)
    _ = logging.getLogger("pytf_logger")
    # before doing anything, make sure token file is up-to-date
    # This is important because a rerun may move an info file and cause a token file to point to
    # a non-existent file
    PyTfToken.update_token_usage(config)


def main(config: Config):
    logger = logging.getLogger('pytf_logger')

    now = prepare_required_dirs(config)

    end_time = pytz.timezone(config.primary_tz).localize(datetime.datetime(year=now.year,
                                                                           month=now.month,
                                                                           day=now.day,
                                                                           hour=config.end_time_hr,
                                                                           minute=config.end_time_min))
    logger.info(f"Running until {end_time}")
    logger.info(f"{config.run_local=}")
    run_main_loop_until_end(config, end_time, main_function)


def run_main_loop_until_end(config: Config, end_time: datetime, function_to_run):
    logger = logging.getLogger('pytf_logger')
    sleep_time = 10
    while True:
        logger.info("Entering main PyTF Loop")
        # primary_tz is used for the start and end time of the main loop
        now: datetime.datetime = MockDateTime.now(config.primary_tz)
        todays_family_dir = dirs.dated_dir(os.path.join(config.family_dir, "{YYYY}{MM}{DD}"), now)
        dirs.copy_files_from_dir_to_dir(config.family_dir, todays_family_dir)
        if now >= end_time:
            break

        function_to_run(config)  # Assume this takes less than a minute to run

        if config.once_only:
            logger.info("Once_only is set. Exiting loop now.")
            break

        now: datetime.datetime = MockDateTime.now(tz=config.primary_tz)
        sleep_time_left = sleep_time - (now.second % sleep_time)
        logger.info(f"Sleeping for {sleep_time_left}")
        MockSleep.sleep(sleep_time_left)


def main_function(config: Config):
    logger = logging.getLogger('pytf_logger')
    status, families, new_token_doc = status_and_families_and_token_doc(config)
    ready_jobs = [j for j in status['status']['flat_list'] if j['status'] in ['Ready', 'Released']]

    if not ready_jobs:
        return

    PyTfToken.save_token_document(config, new_token_doc)

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
                                     f"{job['family_name']}.{job['job_name']}.{job['queue_name']}.x.{start_small}.info")

            # if tokens_needed := job['tokens']:
            #     logger.info(f"Checking for tokens {tokens_needed} for job: {job['family_name']}::{job['job_name']}")
            #     tokens_available = PyTfToken.consume_token(config, tokens_needed, info_path)
            #     if not tokens_available:
            #         logger.warning(f"Not queuing job {job['family_name']}::{job['job_name']} - waiting on tokens")
            #         continue

            with open(info_path, "w") as f:
                f.write(f'family_name = "{job['family_name']}"\n')
                f.write(f'job_name = "{job['job_name']}"\n')
                f.write(f'queue_name = "{job['queue_name']}"\n')
                f.write(f'tz = "{job['tz']}"\n')
                f.write(f'worker_name = "???"\n')
                f.write(f'start_time = "{start_pretty}"\n')
            err = run_shell_script(script_path)
            with open(info_path, "a") as f:
                f.write(f'error_code = {err}\n')
        else:
            now = MockDateTime.now(config.primary_tz)
            start_small = now.strftime("%Y%m%d%H%M%S")
            info_path = os.path.join(config.todays_log_dir,
                                     f"{job['family_name']}.{job['job_name']}.{job['queue_name']}.x.{start_small}.info")

            # if tokens_needed := job['tokens']:
            #     logger.info(f"Checking for tokens {tokens_needed} for job: {job['family_name']}::{job['job_name']}")
            #     tokens_available = PyTfToken.consume_token(config, tokens_needed, info_path)
            #     if not tokens_available:
            #         logger.warning(f"Not queuing job {job['family_name']}::{job['job_name']} - waiting on tokens")
            #         continue

            logger.info(f"Queuing job {job['family_name']}::{job['job_name']} on queue: {job['queue_name']}")
            run_task.apply_async(args=[config.todays_log_dir,
                                       config.job_dir,
                                       config.primary_tz,
                                       job['family_name'],
                                       job['job_name'],
                                       job['tz'],
                                       job['queue_name'],
                                       job_log_file,
                                       info_path],
                                 queue=job['queue_name'])
