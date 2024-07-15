import datetime
import os.path

import tomlkit
from attrs import asdict

from .config import Config
import pytf.dirs as dirs
from .family import Family, get_families_from_dir
from .job_result import JobResult, serializer
from .job_status import JobStatus
from .logs import get_logged_job_results, get_held_jobs, get_released_jobs
from .mockdatetime import MockDateTime
from .runner import prepare_required_dirs
from .pytftoken import PyTfToken


def status(config: Config, dt: datetime.datetime = None):
    status, _, _ = _status_helper(config, dt)
    return status


def status_and_families_and_token_doc(config: Config, dt: datetime.datetime = None):
    return _status_helper(config, dt)


def _status_helper(config: Config, dt: datetime.datetime = None):
    if dt is None:
        dt = MockDateTime.now(config.primary_tz)

    result = {"status": {"flat_list": [], "family": {}}}

    prepare_required_dirs(config)
    new_token_doc = tomlkit.TOMLDocument()

    # To see what's run, don't consult families. Things might have changed.
    # Look at the log dir
    log_dir_to_examine = config.todays_log_dir

    all_families: [Family] = get_families_from_dir(config.todays_family_dir, config)

    # only include families that will run today
    families = [f for f in all_families if f.will_family_run_today()]

    _get_status(config, families, log_dir_to_examine, result)

    # convert ready to token wait if necessary
    token_doc = PyTfToken.current_token_document(config)
    for job_result_dict in result['status']['flat_list']:
        if job_result_dict['status'] == 'Ready':
            if tokens := job_result_dict['tokens']:
                new_token_doc = PyTfToken.consume_tokens_from_doc(config,
                                                                  tokens,
                                                                  token_doc,
                                                                  job_result_dict['family_name'],
                                                                  job_result_dict['job_name'])
                if new_token_doc is not None:
                    token_doc = new_token_doc
                else:
                    job_result_dict['status'] = 'Token Wait'

    return result, families, token_doc


def _get_status(config, families, log_dir, result):
    logged_jobs_list, logged_jobs_dict = get_logged_job_results(log_dir)
    held_jobs = get_held_jobs(log_dir)
    released_jobs = get_released_jobs(log_dir)

    for family in families:
        _get_family_status(config, family, logged_jobs_dict, held_jobs, released_jobs, result)


def _get_family_status(config, family, logged_jobs_dict, held_jobs, released_jobs, result):
    result['status']['family'][family.name] = []

    def coalesce(*args):
        for arg in args:
            if arg is not None:
                return arg

    for job_name in sorted(family.jobs_by_name.keys()):
        job_queue = family.jobs_by_name[job_name].queue
        job_tz = family.jobs_by_name[job_name].tz or family.tz or config.primary_tz
        job_num_retries = coalesce(family.jobs_by_name[job_name].num_retries, family.config.num_retries)
        job_retry_sleep = coalesce(family.jobs_by_name[job_name].retry_sleep, family.config.retry_sleep)
        _get_job_status(family=family,
                        job_name=job_name,
                        logged_jobs_dict=logged_jobs_dict,
                        held_jobs=held_jobs,
                        released_jobs=released_jobs,
                        job_queue=job_queue,
                        job_tz=job_tz,
                        job_num_retries=job_num_retries,
                        job_retry_sleep=job_retry_sleep,
                        result=result)


def _get_job_status(family,
                    job_name,
                    logged_jobs_dict,
                    held_jobs,
                    released_jobs,
                    job_queue,
                    job_tz,
                    job_num_retries,
                    job_retry_sleep,
                    result):
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

        job_status = JobStatus.RELEASED if released else JobStatus.HOLD if held else JobStatus.WAITING if unmet else JobStatus.READY

        the_job_result = JobResult(family_name=family_name,
                                   job_name=job_name,
                                   status=job_status,
                                   queue_name=job_queue,
                                   tz=job_tz,
                                   num_retries=job_num_retries,
                                   retry_sleep=job_retry_sleep,
                                   tokens=family.jobs_by_name[job_name].tokens)
        # noinspection PyTypeChecker
        job_result_dict = asdict(the_job_result, value_serializer=serializer)

    result['status']['flat_list'].append(job_result_dict)
    result['status']['family'][family_name].append(job_result_dict)
