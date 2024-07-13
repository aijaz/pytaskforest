import os
import pathlib
import re

import tomlkit

from .config import Config
from .holdAndRelease import release_dependencies


def rerun(config:Config, family, job):
    """
    A rerun should do the following:
    - Move the old info file to *.Orig-$n.info
    - Release all dependencies on that job
        - This should cause that job to be eligible for the next run
        - A job should not be rerun if it's still running
    :param config:
    :param family:
    :param job:
    :return:
    """
    all_files = os.listdir(config.todays_log_dir)
    all_info_files = [fn for fn in all_files
                      if (fn.startswith(f"{family}.{job}.")
                          or fn.startswith(f"{family}.{job}-Orig-"))
                      and fn.endswith(".info")]
    next_info_number = 1
    r = re.compile(r'-Orig-(\d+)\.')
    existing_info_numbers = [int(re.findall(r, fn)[0]) for fn in all_info_files if re.findall(r, fn)]
    if existing_info_numbers:
        next_info_number = max(existing_info_numbers) + 1

    file_to_rename = [f for f in all_info_files if not re.findall(r, f)]
    if file_to_rename:
        new_job_name = f'{job}-Orig-{next_info_number}'
        l = file_to_rename[0].split(".")
        l[1] = new_job_name
        new_file_name = ".".join(l)
        # change the job name to be the new job name
        job_info_str = pathlib.Path(os.path.join(config.todays_log_dir, file_to_rename[0])).read_text()
        job_info = tomlkit.loads(job_info_str)
        if job_info.get('error_code') is None:
            # don't rerun if the job is still running
            return
        job_info['job_name'] = new_job_name
        os.remove(os.path.join(config.todays_log_dir, file_to_rename[0]))
        with open(os.path.join(config.todays_log_dir, new_file_name), "w") as f:
            f.write(tomlkit.dumps(job_info))

        release_dependencies(config, family, job)
