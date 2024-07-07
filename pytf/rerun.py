import os
import re
import shutil

from .config import Config
from .holdAndRelease import release_dependencies

def rerun(config:Config, family, job):
    """
    A rerun should do the following:
    - Move the old info file to *.Orig-$n.info
    - Release all dependencies on that job
        - This should cause that job to be eligible for the next run
    :param config:
    :param family:
    :param job:
    :return:
    """
    all_files = os.listdir(config.todays_log_dir)
    all_info_files = [fn for fn in all_files
                      if fn.startswith(f"{family}.{job}.")]
    next_info_number = 1
    r = re.compile(r'\.Orig-(\d+)\.info')
    existing_info_numbers = [int(re.findall(r, fn)[0]) for fn in all_info_files if re.findall(r, fn)]
    if existing_info_numbers:
        next_info_number = max(existing_info_numbers) + 1

    file_to_rename = [f for f in all_info_files if not re.findall(r, f)]
    if file_to_rename:
        l = file_to_rename[0].split(".")
        l[-1] = f"Orig[{next_info_number}.info"
        new_file_name = ".".join(l)
        os.rename(os.path.join(config.todays_log_dir, file_to_rename[0]),
                  os.path.join(config.todays_log_dir, new_file_name))

        release_dependencies(config, family, job)
