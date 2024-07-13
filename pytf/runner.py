import datetime
import os

import pytf.dirs as dirs
from .mockdatetime import MockDateTime


def prepare_required_dirs(config):
    now: datetime.datetime = MockDateTime.now(tz=config.primary_tz)
    todays_family_dir = dirs.dated_dir(os.path.join(config.family_dir, "{YYYY}{MM}{DD}"), now)
    _make_family_dir_if_necessary(todays_family_dir)
    todays_log_dir = dirs.dated_dir(os.path.join(config.log_dir, "{YYYY}{MM}{DD}"), now)
    dirs.make_dir_if_necessary(todays_log_dir)
    config.todays_log_dir = todays_log_dir
    config.todays_family_dir = todays_family_dir
    return now


def _make_family_dir_if_necessary(todays_family_dir):
    if not dirs.does_dir_exist(todays_family_dir):
        dirs.make_dir(todays_family_dir)

