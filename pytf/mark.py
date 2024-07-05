import os

import pathlib
import tomlkit

from .config import Config
from .mockdatetime import MockDateTime
import pytf.exceptions as ex


def mark(config:Config, family_name:str, job_name:str, error_code:int):
    all_files = os.listdir(config.todays_log_dir)
    info_files = [f for f in all_files
                  if f.startswith(f"{family_name}.{job_name}") and
                  f.endswith(".info")]
    if len(info_files) != 1:
        raise ex.PyTaskforestParseException(f"{ex.MSG_CANT_FIND_SINGLE_JOB_INFO_FILE} {family_name}:{job_name}")

    info_path = os.path.join(config.todays_log_dir, info_files[0])
    job_toml_str = pathlib.Path(info_path).read_text()
    job_dict = tomlkit.loads(job_toml_str)
    old_error_code = job_dict['error_code']
    job_dict['error_code'] = error_code
    now_str = MockDateTime.now(tz=config.primary_tz).strftime("%Y%m%d_%H%M%S")
    job_dict[f"original_error_code_{now_str}"] = old_error_code
    with open(info_path, "w") as f:
        f.write(tomlkit.dumps(job_dict))
