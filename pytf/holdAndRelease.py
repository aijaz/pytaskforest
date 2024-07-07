import os

from .config import Config


def hold(config:Config, family, job):
    _hold_or_release(config, family, job, 'hold', 'release')


def release_dependencies(config:Config, family, job):
    _hold_or_release(config, family, job, 'release', 'hold')


def remove_hold(config:Config, family, job):
    primary_name = os.path.join(config.todays_log_dir, f"{family}.{job}.hold")
    if os.path.exists(primary_name):
        os.remove(primary_name)


def _hold_or_release(config:Config, family, job, primary, secondary):
    primary_name = os.path.join(config.todays_log_dir, f"{family}.{job}.{primary}")
    secondary_file_name = os.path.join(config.todays_log_dir, f"{family}.{job}.{secondary}")
    with open(primary_name, "w") as f:
        f.write("")
        if os.path.exists(secondary_file_name):
            os.remove(secondary_file_name)
