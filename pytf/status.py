import datetime
import os.path

from attrs import asdict

from .config import Config
import pytf.dirs as dirs
from .family import get_families_from_dir
from .job_result import JobResult, serializer
from .job_status import JobStatus
from .logs import get_logged_job_results
from .mockdatetime import MockDateTime


def status(config: Config, dt: datetime.datetime=None):
    if dt is None:
        dt = MockDateTime.now(config.primary_tz)

    result = { "status" : { "flat_list": [], "family" : {}}}

    # To see what's run, don't consult families. Things might have changed.
    # Look at the log dir
    log_dir_to_examine = dirs.dated_subdir(config.log_dir, dt)
    if not os.path.exists(log_dir_to_examine):
        return result

    family_dir = dirs.dated_subdir(config.family_dir, dt)
    families = get_families_from_dir(family_dir, config)

    _get_status(families, log_dir_to_examine, result)

    return result


def _get_status(families, log_dir, result):
    logged_jobs_list, logged_jobs_dict = get_logged_job_results(log_dir)

    for family in families:
        _get_family_status(family, logged_jobs_dict, result)


def _get_family_status(family, logged_jobs_dict, result):
    result['status']['family'][family.name] = []

    for job_name in sorted(family.jobs_by_name.keys()):
        job_queue = family.jobs_by_name[job_name].queue
        _get_job_status(family, job_name, logged_jobs_dict, job_queue, result)


def _get_job_status(family, job_name, logged_jobs_dict, job_queue, result):
    family_name = family.name
    if logged_jobs_dict.get(family_name) and logged_jobs_dict[family_name].get(job_name):
        job_result_dict = asdict(logged_jobs_dict[family_name].get(job_name), value_serializer=serializer)
    else:
        unmet = [True for d in family.jobs_by_name[job_name].dependencies if d.met(logged_jobs_dict) is False]

        the_job_result = JobResult(family_name, job_name, JobStatus.WAITING if unmet else JobStatus.READY, job_queue)
        # noinspection PyTypeChecker
        job_result_dict = asdict(the_job_result, value_serializer=serializer)

    result['status']['flat_list'].append(job_result_dict)
    result['status']['family'][family_name].append(job_result_dict)
