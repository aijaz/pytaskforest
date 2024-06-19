import datetime
import os.path

from pytf.pytf.config import Config
from pytf.pytf.dirs import (
    todays_family_dir,
    dated_subdir,
)
from pytf.pytf.mockdatetime import MockDateTime


def status(config: Config, dt: datetime.datetime=None):
    if dt is None:
        dt = MockDateTime.now(config.primary_tz)

    # To see what's run, don't consult families. Things might have changed.
    # Look at the log dir
    log_dir_to_examine = dated_subdir(config.log_dir, dt)
    if not os.path.exists(log_dir_to_examine):
        return None

    # logged_jobs = get_logged_jobs(log_dir_to_examine)
    #
    # if not config.families
    # log_dir = todays_log_dir(config=config)

    # get all jobs from today's family_dir
    # read log_dir
