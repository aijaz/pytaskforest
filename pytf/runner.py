import datetime
import os
import subprocess

import pytf.dirs as dirs
from .mockdatetime import MockDateTime


def prepare_required_dirs(config):
    now: datetime.datetime = MockDateTime.now(tz=config.primary_tz)
    todays_family_dir = dirs.dated_dir(os.path.join(config.family_dir, "{YYYY}{MM}{DD}"), now)
    _make_family_dir_if_necessary(config, todays_family_dir)
    todays_log_dir = dirs.dated_dir(os.path.join(config.log_dir, "{YYYY}{MM}{DD}"), now)
    dirs.make_dir_if_necessary(todays_log_dir)
    config.todays_log_dir = todays_log_dir
    config.todays_family_dir = todays_family_dir
    return now


def _make_family_dir_if_necessary(config, todays_family_dir):
    if not dirs.does_dir_exist(todays_family_dir):
        dirs.make_dir(todays_family_dir)
        dirs.copy_files_from_dir_to_dir(config.family_dir, todays_family_dir)


def run_shell_script(script_path, run_logger):

    process = subprocess.Popen(
        script_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    while True:
        if line := process.stdout.readline().decode('utf-8').strip():
            run_logger.info(line)
        if line := process.stderr.readline().decode('utf-8').strip():
            run_logger.error(line)
        if (err_code := process.poll()) is not None:
            # clean up any remaining lines from the buffers
            while line := process.stdout.readline().decode('utf-8').strip():
                run_logger.info(line)
            while line := process.stderr.readline().decode('utf-8').strip():
                run_logger.error(line)
            if err_code:
                run_logger.error(f"Process failed with error code {err_code}")
            else:
                run_logger.info(f"Process completed with return code {err_code}")
            break
        time.sleep(0.1)

    process.stdout.close()
    process.stderr.close()
    return err_code

