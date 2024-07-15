import os

import pathlib
import tomlkit

import pytf.dirs as dirs
from .job_result import JobResult
from .job_status import JobStatus


def get_held_jobs(log_dir: str):
    held_jobs = {}
    held_files = [(fn.split(".")) for fn in os.listdir(log_dir) if fn.endswith(".hold")]
    for f, j, _ in held_files:
        if held_jobs.get(f) is None:
            held_jobs[f] = {}
        held_jobs[f][j] = True
    return held_jobs


def get_released_jobs(log_dir: str):
    released_jobs = {}
    released_files = [(fn.split(".")) for fn in os.listdir(log_dir) if fn.endswith(".release")]
    for f, j, _ in released_files:
        if released_jobs.get(f) is None:
            released_jobs[f] = {}
        released_jobs[f][j] = True
    return released_jobs


def get_logged_job_results(log_dir: str) -> ([JobResult], dict[str, object]):
    """
    File names are FamilyName.JobName.queue.worker_name.start_time_local.info
    File names are FamilyName.JobName.queue.worker_name.start_time_local.log

    :param log_dir:
    :return:
    """
    files = dirs.list_of_files_in_dir(log_dir)
    prefixes = [file_name[:-5] for file_name in files if file_name.endswith('.info')]
    job_array = []
    job_dict = {}

    for prefix in prefixes:
        job_info_str = pathlib.Path(os.path.join(log_dir, f"{prefix}.info")).read_text()
        print(job_info_str)
        job_info = tomlkit.loads(job_info_str)
        status = JobStatus.RUNNING
        error_code = job_info.get('error_code')

        if error_code is not None:
            status = JobStatus.FAILURE if error_code else JobStatus.SUCCESS
            error_code = job_info['error_code']

        if job_info.get('retry_wait_until'):
            status = JobStatus.RETRY_WAIT

        job_result = JobResult(family_name=job_info['family_name'],
                               job_name=job_info['job_name'],
                               status=status,
                               tz=job_info['tz'],  # this will always be config.primary_tz
                               queue_name=job_info['queue_name'],
                               num_retries=job_info['num_retries'],
                               retry_sleep=job_info['retry_sleep'],
                               worker_name=job_info['worker_name'],
                               error_code=error_code,
                               start_time=job_info["start_time"],
                               )
        if not job_dict.get(job_result.family_name):
            job_dict[job_result.family_name] = {}
        job_dict[job_result.family_name][job_result.job_name] = job_result
        job_array.append(job_result)

    return job_array, job_dict
