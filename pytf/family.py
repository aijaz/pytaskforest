import re

from attrs import define, field
import tomlkit
import tomlkit.exceptions
import tomlkit.items

from .forest import Forest
import pytf.exceptions as ex
from .parse_utils import parse_time, lower_true_false, simple_type
from .config import Config
from .calendar import Calendar
from .days import Days
from .job import Job
import pytf.dirs as dirs

@define
class Family:
    """
    A job name must only appear once in a family file.
    If a job name appears more than once, it's an error.
    The user should change it so that the job names are unique.
    """
    name: str = field()
    start_time_hr: int = field()
    start_time_min: int = field()
    tz: str = field()
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
    start_time_met_today: bool = field(default=False)

    @classmethod
    def parse(cls, family_name: str, family_str: str, config: Config):
        fam = cls(
            name=family_name,
            start_time_hr=0,
            start_time_min=0,
            tz=''
        )
        lines = family_str.split("\n")

        first_line = lines.pop(0)
        first_line = lower_true_false(first_line)

        first_line_toml_str = f'd = {{ {first_line} }}'

        try:
            toml_d = tomlkit.loads(first_line_toml_str)
        except tomlkit.exceptions.UnexpectedEofError as e:
            raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_FIRST_LINE_PARSE_FAIL} {first_line}") from e

        d = toml_d.get('d')

        cls.validate_inner_params(d)

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
                rules = config['calendars'][calendar_name]
            except KeyError as e:
                raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_UNKNOWN_CALENDAR} {calendar_name}") from e

            fam.calendar_or_days = Calendar(calendar_name, rules=rules)
        elif d.get('days'):
            fam.calendar_or_days = Days(days=d['days'])
        else:
            fam.calendar_or_days = Days(days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

        # parse the rest of the lines
        fam.forests = [Forest(jobs=[])]
        strip_comments_pattern = re.compile('#.*')
        dashes_pattern = re.compile('^[- ]+$')

        for line in lines:
            line = re.sub(strip_comments_pattern, '', line).strip()
            if not line:
                continue

            if dashes_pattern.match(line):
                # new family
                if len(fam.forests[-1].jobs) > 0:
                    fam.forests.append(Forest(jobs=[]))
                continue

            # now we have a line of jobs
            jobs = Forest.split_jobs(line)
            fam.forests[-1].jobs.append(jobs)

        # get rid of last forest if it has no jobs
        if len(fam.forests[-1].jobs) == 0:
            fam.forests.pop()


        internal_jobs = fam.get_all_internal_jobs()
        for job in internal_jobs:
            if fam.jobs_by_name.get(job.job_name):
                raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_JOB_TWICE} {fam.name}::{job.job_name}")
            fam.jobs_by_name[job.job_name] = job

        return fam

    @classmethod
    def validate_inner_params(cls, d):
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

        strs = [
            'tz',
            'queue',
            'email',
            'retry_email',
            'retry_success-email',
            'comment',
            'calendar',
        ]

        str_lists = [
            'days',
        ]

        bools = [
            'no_retry_email',
            'no_retry_success_email',
        ]

        for key in strs:
            if key in d and type(d[key]) is not tomlkit.items.String:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_FAMILY_INVALID_TYPE} {key} ({d[key]}) is type {simple_type(d[key])}")

        for key in bools:
            if key in d and type(d[key]) is not bool:
                raise ex.PyTaskforestParseException(
                    f"{ex.MSG_FAMILY_INVALID_TYPE} {key} ({d[key]}) is type {simple_type(d[key])}")

        for key in str_lists:
            if key in d:
                for i in d[key]:
                    if type(i) is not tomlkit.items.String:
                        raise ex.PyTaskforestParseException(f"{ex.MSG_FAMILY_INVALID_TYPE} {key} ({d[key]} :: {i})")

        if d.get('calendar') and d.get('days'):
            raise ex.PyTaskforestParseException(ex.MSG_FAMILY_CAL_AND_DAYS)

    def get_all_internal_jobs(self) -> [Job]:
        result = []
        for forest in self.forests:
            result.extend(forest.get_all_internal_jobs())
        return result


def get_families_from_dir(family_dir: str, config: Config) -> [Family]:
    files = dirs.text_files_in_dir(family_dir, config.ignore_regex)
    files.sort(key=lambda tup: tup[0])
    return [Family.parse(family_name=item[0], family_str=item[1], config=config) for item in files]


