import datetime
import os.path

from attrs import asdict

from .config import Config
import pytf.dirs as dirs
from .family import get_families_from_dir
from .job_result import JobResult, serializer
from .job_status import JobStatus
from .logs import get_logged_job_results, get_held_jobs, get_released_jobs
from .mockdatetime import MockDateTime
from .runner import prepare_required_dirs


def status(config: Config, dt: datetime.datetime = None):
    status, _ = _status_helper(config, dt)
    return status


def status_and_families(config: Config, dt: datetime.datetime = None):
    return _status_helper(config, dt)


def _status_helper(config: Config, dt: datetime.datetime = None):
    if dt is None:
        dt = MockDateTime.now(config.primary_tz)

    result = {"status": {"flat_list": [], "family": {}}}

    prepare_required_dirs(config)

    # To see what's run, don't consult families. Things might have changed.
    # Look at the log dir
    log_dir_to_examine = dirs.dated_subdir(config.log_dir, dt)
    if not os.path.exists(log_dir_to_examine):
        return result, []

    families = get_families_from_dir(config.todays_family_dir, config)

    _get_status(config, families, log_dir_to_examine, result)

    return result, families


def _get_status(config, families, log_dir, result):
    logged_jobs_list, logged_jobs_dict = get_logged_job_results(log_dir)
    held_jobs = get_held_jobs(log_dir)
    released_jobs = get_released_jobs(log_dir)

    for family in families:
        _get_family_status(config, family, logged_jobs_dict, held_jobs, released_jobs, result)


def _get_family_status(config, family, logged_jobs_dict, held_jobs, released_jobs, result):
    result['status']['family'][family.name] = []

    for job_name in sorted(family.jobs_by_name.keys()):
        job_queue = family.jobs_by_name[job_name].queue
        job_tz = family.jobs_by_name[job_name].tz or family.tz or config.primary_tz
        _get_job_status(family, job_name, logged_jobs_dict, held_jobs, released_jobs, job_queue, job_tz, result)


def _get_job_status(family, job_name, logged_jobs_dict, held_jobs, released_jobs, job_queue, job_tz, result):
    family_name = family.name
    if logged_jobs_dict.get(family_name) and logged_jobs_dict[family_name].get(job_name):
        job_result_dict = asdict(logged_jobs_dict[family_name].get(job_name), value_serializer=serializer)
    else:
        unmet = [True for d in family.jobs_by_name[job_name].dependencies if d.met(logged_jobs_dict) is False]
        held = bool(
            held_jobs.get(family_name) and held_jobs[family_name].get(job_name)
        )
        released = bool(
            released_jobs.get(family_name) and released_jobs[family_name].get(job_name)
        )
        the_job_result = JobResult(family_name,
                                   job_name,
                                   JobStatus.READY if released
                                   else JobStatus.HOLD if held
                                   else JobStatus.WAITING if unmet
                                   else JobStatus.READY,
                                   job_queue,
                                   job_tz)
        # noinspection PyTypeChecker
        job_result_dict = asdict(the_job_result, value_serializer=serializer)

    result['status']['flat_list'].append(job_result_dict)
    result['status']['family'][family_name].append(job_result_dict)
