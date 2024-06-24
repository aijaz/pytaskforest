import os
import re

from attrs import define, field
import tomlkit
import tomlkit.exceptions
import tomlkit.items

from .forest import Forest
import pytf.exceptions as ex
from .parse_utils import parse_time, lower_true_false, simple_type
from .config import Config
from .pytf_calendar import Calendar
from .dependency import JobDependency, TimeDependency
from .days import Days
from .job import Job
import pytf.logs
from .mockdatetime import MockDateTime
import pytf.dirs as dirs


@define
class Family:
    """
    A job name must only appear once in a family file.
    If a job name appears more than once, it's an error.
    The user should change it so that the job names are unique.
    """
    name: str = field()
    tz: str = field()
    start_time_hr: int = field(default=0)
    start_time_min: int = field(default=0)
    calendar_or_days: Calendar | Days | None = field(default=None)
    queue: str | None = field(default=None)
    email: str | None = field(default=None)
    retry_email: str | None = field(default=None)
    retry_success_email: str | None = field(default=None)
    no_retry_email: bool | None = field(default=None)
    no_retry_success_email: bool | None = field(default=None)
    forests: [Forest] = field(default=None)
    comment: str | None = field(default=None)
    jobs_by_name: dict = field()

    @jobs_by_name.default
    def _jobs_by_name_default(self):
        return {}

    # dynamic fields
    config: Config | None = field(default=None)

    @classmethod
    def parse(cls, family_name: str, family_str: str, config: Config):
        fam = cls(
            name=family_name,
            start_time_hr=0,
            start_time_min=0,
            tz='',
            config=config
        )

        lines = family_str.split("\n")
        first_line = lines.pop(0)

        d = cls._dictionary_from_first_line(first_line)
        cls._validate_inner_params(d)
        cls._populate_family_attrs_from_dict(fam, d)

        # parse the rest of the lines
        cls._populate_family_forests(fam, family_name, lines)

        cls._set_jobs_by_name(fam)

        return fam

    @classmethod
    def _set_jobs_by_name(cls, fam):
        internal_jobs = fam._get_all_internal_jobs()
        for job in internal_jobs:
            if fam.jobs_by_name.get(job.job_name):
                raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_JOB_TWICE} {fam.name}::{job.job_name}")
            fam.jobs_by_name[job.job_name] = job

    @classmethod
    def _populate_family_forests(cls, fam, family_name, lines):
        fam.forests = [Forest(jobs=[])]

        cls._create_forests_from_lines(fam, family_name, lines)

        # get rid of last forest if it has no jobs
        if len(fam.forests[-1].jobs) == 0:
            fam.forests.pop()

        # set up dependencies
        for forest in fam.forests:
            cls._setup_forest_dependencies(fam, forest)

    @classmethod
    def _setup_forest_dependencies(cls, fam, forest):
        last_job_dependency_set = set()
        for job_line in forest.jobs:
            last_job_dependency_set = cls._create_dependencies_for_job_line(fam, job_line, last_job_dependency_set)

    @classmethod
    def _create_dependencies_for_job_line(cls, fam, job_line, last_job_dependency_set) -> set:
        for job_or_external_dependency in job_line:
            if not isinstance(job_or_external_dependency, Job):
                continue

            # add job dependency(ies)
            job_or_external_dependency.dependencies = set(last_job_dependency_set)

            # add time dependencies
            cls._add_time_dependencies_for_job(fam, job_or_external_dependency)

        # return new last_job_dependency_set
        return {
            JobDependency(fam.config, fam.name, i.job_name)
            if isinstance(i, JobDependency)
            else JobDependency(fam.config, i.family_name, i.job_name)
            for i in job_line
        }

    @classmethod
    def _add_time_dependencies_for_job(cls, fam, job: Job):

        if job.start_time_hr is not None and job.start_time_min is not None:
            tz = job.tz or fam.tz or fam.config.primary_tz
            job.dependencies.add(TimeDependency(fam.config, job.start_time_hr, job.start_time_min, tz))

        if fam.start_time_hr is not None and fam.start_time_min is not None:
            tz = fam.tz or fam.config.primary_tz
            job.dependencies.add(TimeDependency(fam.config, fam.start_time_hr, fam.start_time_min, tz))

    @classmethod
    def _create_forests_from_lines(cls, fam, family_name, lines):
        comments_pattern = re.compile(r'#.*$')
        dashes_pattern = re.compile('^[- ]+$')

        non_comment_lines = map(lambda x: re.sub(comments_pattern, '', x).strip(), lines)
        non_blank_non_comment_lines = filter(lambda x: x, non_comment_lines)
        for line in non_blank_non_comment_lines:

            if dashes_pattern.match(line):
                # new forest
                # only create a new forest if the last forest has 1 or more jobs
                if len(fam.forests[-1].jobs) > 0:
                    fam.forests.append(Forest(jobs=[]))
                continue

            # now we have a line of jobs
            jobs = Forest.split_jobs(line, family_name)
            # named_jobs = map(lambda j: cls._assign_family_name_to_internal_job(j, family_name), jobs)
            fam.forests[-1].jobs.append(list(jobs))

    @classmethod
    def _populate_family_attrs_from_dict(cls, fam, d):
        fam.start_time_hr, fam.start_time_min = parse_time(d,
                                                           "",
                                                           'start',
                                                           ex.MSG_FAMILY_START_TIME_PARSING_FAILED)
        fam.tz = d.get('tz')
        fam.queue = d.get('queue')
        fam.retry_email = d.get('retry_email')
        fam.email = d.get('email')
        fam.retry_success_email = d.get('retry_success-email')
        fam.no_retry_email = d.get('no_retry_email')
        fam.no_retry_success_email = d.get('no_retry_success_email')
        fam.comment = d.get('comment')
        if d.get('calendar'):
            calendar_name = d['calendar']
            try:
                rules = fam.config['calendars'][calendar_name]
            except KeyError as e:
                raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_UNKNOWN_CALENDAR} {calendar_name}") from e

            fam.calendar_or_days = Calendar(calendar_name, rules=rules)
        elif d.get('days'):
            fam.calendar_or_days = Days(days=d['days'])
        else:
            fam.calendar_or_days = Days(days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

    @classmethod
    def _dictionary_from_first_line(cls, first_line):
        first_line = lower_true_false(first_line)
        first_line_toml_str = f'd = {{ {first_line} }}'
        try:
            toml_d = tomlkit.loads(first_line_toml_str)
        except tomlkit.exceptions.UnexpectedEofError as e:
            raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_FIRST_LINE_PARSE_FAIL} {first_line}") from e
        return toml_d.get('d')

    @classmethod
    def _validate_inner_params(cls, d):
        cls.confirm_all_keys_are_known(d)
        cls.validate_string_params(d)
        cls.validate_string_list_params(d)
        cls.validate_bool_params(d)

        if d.get('calendar') and d.get('days'):
            raise ex.PyTaskforestParseException(ex.MSG_FAMILY_CAL_AND_DAYS)

    @classmethod
    def validate_bool_params(cls, d):
        bools = [
            'no_retry_email',
            'no_retry_success_email',
        ]
        for key in bools:
            if key in d and type(d[key]) is not bool:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_FAMILY_INVALID_TYPE} {key} ({d[key]}) is type {simple_type(d[key])}")

    @classmethod
    def validate_string_list_params(cls, d):
        str_lists = [
            'days',
        ]
        for key in [i for i in str_lists if i in d]:
            for i in d[key]:
                if type(i) is not tomlkit.items.String:
                    raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_INVALID_TYPE} {key} ({d[key]} :: {i})")

    @classmethod
    def validate_string_params(cls, d):
        strs = [
            'tz',
            'queue',
            'email',
            'retry_email',
            'retry_success-email',
            'comment',
            'calendar',
        ]
        for key in strs:
            if key in d and type(d[key]) is not tomlkit.items.String:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_FAMILY_INVALID_TYPE} {key} ({d[key]}) is type {simple_type(d[key])}")

    @classmethod
    def confirm_all_keys_are_known(cls, d):
        valid_keys = [
            'start',
            'tz',
            'calendar',
            'days',
            'queue',
            'email',
            'retry_email',
            'retry_success-email',
            'no_retry_email',
            'no_retry_success_email',
            'comment',
        ]
        for key in d:
            if key not in valid_keys:
                raise (ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_UNRECOGNIZED_PARAM}: {key}"))

    def _get_all_internal_jobs(self) -> [Job]:
        result = []
        for forest in self.forests:
            result.extend(forest._get_all_internal_jobs())
        return result

    def names_of_all_ready_jobs(self):
        result = []

        dt = MockDateTime.now(self.config.primary_tz)

        log_dir_to_examine = dirs.dated_subdir(self.config.log_dir, dt)
        if not os.path.exists(log_dir_to_examine):
            return None

        logged_jobs_list, logged_jobs_dict = pytf.logs.get_logged_job_results(log_dir_to_examine)

        for job_name in self.jobs_by_name:
            if logged_jobs_dict.get(self.name) and logged_jobs_dict[self.name].get(job_name):
                # already ran, or running
                continue
            unmet = [True for d in self.jobs_by_name[job_name].dependencies if d.met(logged_jobs_dict) is False]
            if unmet:
                continue
            result.append(job_name)

        return result


def get_families_from_dir(family_dir: str, config: Config) -> [Family]:
    files = dirs.text_files_in_dir(family_dir, config.ignore_regex)
    files.sort(key=lambda tup: tup[0])
    return [Family.parse(family_name=item[0], family_str=item[1], config=config) for item in files]
