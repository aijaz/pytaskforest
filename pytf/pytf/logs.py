import os

import pathlib
import tomlkit

from .dirs import (
    list_of_files_in_dir,
)
from .job_result import JobResult
from .job_status import JobStatus


def get_logged_job_results(log_dir: str) -> [JobResult]:
    """
    File names are FamilyName.JobName.queue.worker_name.start_time_local.info
    File names are FamilyName.JobName.queue.worker_name.start_time_local.log

    :param log_dir:
    :return:
    """
    files = list_of_files_in_dir(log_dir)
    prefixes = [file_name[:-5] for file_name in files if file_name.endswith('.info')]
    job_results = []
    for prefix in prefixes:
        job_info_str = pathlib.Path(os.path.join(log_dir, f"{prefix}.info")).read_text()
        job_info = tomlkit.loads(job_info_str)
        status = JobStatus.RUNNING
        error_code = job_info.get('error_code')

        if error_code is not None:
            status = JobStatus.FAILURE if error_code else JobStatus.SUCCESS
            error_code = job_info['error_code']

        job_result = JobResult(family_name=job_info['family_name'],
                               job_name=job_info['job_name'],
                               tz=job_info['tz'],
                               queue_name=job_info['queue_name'],
                               worker_name=job_info['worker_name'],
                               status=status,
                               error_code=error_code,
                               start_time=job_info["start_time"],
                               )

        job_results.append(job_result)

    return job_results