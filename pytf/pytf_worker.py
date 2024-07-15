from datetime import datetime, timezone
import logging
import logging.config
import os
import pathlib
import subprocess
import time

from celery import Celery
import pytz
import tomlkit

celery_app = Celery('celery_worker', broker='pyamqp://guest:guest@rabbitmq_c//')


def run(todays_log_dir: str,
        job_dir: str,
        primary_tz: str,
        family_name: str,
        job_name: str,
        job_tz: str,
        job_queue_name: str,
        job_num_retries: int,
        job_retry_sleep: int,
        job_log_file: str,
        info_path: str):
    runs_completed = 0
    run_logger = logging.getLogger('run_logger')
    run_logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename=job_log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"))
    handler.setLevel(logging.INFO)
    for old_handler in run_logger.handlers:
        run_logger.removeHandler(old_handler)
    run_logger.addHandler(handler)
    run_logger.propagate = False

    script_path = os.path.join(job_dir, job_name)
    worker_pid = os.getpid()
    total_tries = 1 + job_num_retries

    while runs_completed < total_tries:
        run_logger.info(f"Run Logger: Worker gonna run job {family_name}::{job_name}: {script_path}")
        start_pretty = time_zoned_now().astimezone(pytz.timezone(job_tz)).strftime("%Y/%m/%d %H:%M:%S")

        process = start_process(script_path)
        job_pid = process.pid

        with open(info_path, "w") as f:
            f.write(f'family_name = "{family_name}"\n')
            f.write(f'job_name = "{job_name}"\n')
            f.write(f'queue_name = "{job_queue_name}"\n')
            f.write(f'num_retries = "{job_num_retries}"\n')
            f.write(f'retry_sleep = "{job_retry_sleep}"\n')
            f.write(f'tz = "{job_tz}"\n')
            f.write(f'worker_name = "???"\n')
            f.write(f'worker_pid = {worker_pid}\n')
            f.write(f'job_pid = {job_pid}\n')
            f.write(f'start_time = "{start_pretty}"\n')
            f.write(f'job_log_file = "{job_log_file}"\n')

        err = poll_process(process)

        info_file_str = pathlib.Path(info_path).read_text()
        doc = tomlkit.loads(info_file_str)
        doc['error_code'] = err

        if err == 0:
            run_logger.info(f"Job {family_name}::{job_name} exited with error code 0 - Success")
            with open(info_path, "w") as f:
                f.write(tomlkit.dumps(doc))
                return

        run_logger.error(f"Job {family_name}::{job_name} exited with error code {err}")
        if runs_completed < job_num_retries:
            num_retries_left = job_num_retries - runs_completed
            word = 'retry' if num_retries_left == 1 else 'retries'

            run_logger.info(f"{num_retries_left} {word} left - sleeping for {job_retry_sleep} seconds")
            del doc['job_pid']
            current_epoch = int(time.time())
            doc['retry_wait_until'] = current_epoch + job_retry_sleep

            with open(info_path, "w") as f:
                f.write(tomlkit.dumps(doc))

            runs_completed += 1

            time.sleep(job_retry_sleep)
        else:
            run_logger.error("No more retries. Logging the failure.")
            with open(info_path, "a") as f:
                f.write(f'error_code = {err}\n')
            runs_completed += 1


@celery_app.task(name='celery.run_task')
def run_task(todays_log_dir: str,
             job_dir: str,
             primary_tz: str,
             family_name: str,
             job_name: str,
             job_tz: str,
             job_queue_name: str,
             job_num_retries: int,
             job_retry_sleep: int,
             job_log_file: str,
             job_info_file: str):
    run(todays_log_dir,
        job_dir,
        primary_tz,
        family_name,
        job_name,
        job_tz,
        job_queue_name,
        job_num_retries,
        job_retry_sleep,
        job_log_file,
        job_info_file)


def time_zoned_now(tz: str = "UTC") -> datetime:
    return datetime.now(timezone.utc).astimezone(pytz.timezone(tz))


def start_process(script_path: str):
    return subprocess.Popen(
        script_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def poll_process(process):
    run_logger = logging.getLogger('run_logger')

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
