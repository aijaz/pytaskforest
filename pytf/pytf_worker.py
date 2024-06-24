import logging
import logging.config
import os

from celery import Celery
import pytz

from .pytf_logging import get_logging_config
from .mockdatetime import MockDateTime
from .runner import run_shell_script


celery_app = Celery('celery_worker', broker="amqp://myuser:mypassword@localhost:5672/myvhost")


def run(todays_log_dir: str,
        job_dir: str,
        primary_tz: str,
        family_name: str,
        job_name: str,
        job_tz: str,
        job_queue_name: str,
        job_log_file: str):
    run_logger = logging.getLogger('run_logger')
    run_logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename=job_log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"))
    handler.setLevel(logging.DEBUG)
    for old_handler in run_logger.handlers:
        run_logger.removeHandler(old_handler)
    run_logger.addHandler(handler)
    run_logger.propagate = False

    run_logger.info(f"Run Logger: Gonna run job {family_name}::{job_name} locally")
    script_path = os.path.join(job_dir, job_name)
    now = MockDateTime.now(primary_tz)
    start_small = now.strftime("%Y%m%d%H%M%S")
    start_pretty = MockDateTime.now().astimezone(pytz.timezone(job_tz)).strftime("%Y/%m/%d %H:%M:%S")
    info_path = os.path.join(todays_log_dir,
                             f"{family_name}.{job_name}.x.x.{start_small}.info")

    with open(info_path, "w") as f:
        f.write(f'family_name = "{family_name}"\n')
        f.write(f'job_name = "{job_name}"\n')
        f.write(f'queue_name = "{job_queue_name}"\n')
        f.write(f'tz = "{job_tz}"\n')
        f.write(f'worker_name = "???"\n')
        f.write(f'start_time = "{start_pretty}"\n')
        f.write(f'job_log_file = "{job_log_file}"\n')

    err = run_shell_script(script_path)

    with open(info_path, "a") as f:
        f.write(f'error_code = {err}')


@celery_app.task(name='celery.run_task')
def run_task(todays_log_dir: str,
        job_dir: str,
        primary_tz: str,
        family_name: str,
        job_name: str,
        job_tz: str,
        job_queue_name: str,
        job_log_file: str):
    setup_logging(todays_log_dir)
    run(todays_log_dir,
        job_dir,
        primary_tz,
        family_name,
        job_name,
        job_tz,
        job_queue_name,
        job_log_file)


def setup_logging(log_dir: str):
    logging.config.dictConfig(get_logging_config(log_dir))
    _ = logging.getLogger('runner')


