import pytest

from app.model.job import Job
from app.model.exceptions import (
    PyTaskforestParseException,
    MSG_INNER_PARSING_FAILED,
    MSG_START_TIME_PARSING_FAILED,
)

job_name_parameters = [
    ('simple', ("J_Job()", "J_Job", None)),
    ('all_lower', ("j_job()", "j_job", None)),
    ('all_upper', ("J_JOB()", "J_JOB", None)),
    ('with_number', ("J_JOB1()", "J_JOB1", None)),
    ('start_with_number', ("1J_JOB1()", "1J_JOB1", None)),
    ('numbers_only', ("22()", "22", None)),
    ('with_inner_data', ("J_JOB1(sdfsdfd)", "J_JOB1__PARSE_FAIL", MSG_INNER_PARSING_FAILED)),
    ('with_inner_val', ('J_JOB1(a = "b" )', "J_JOB1", None)),
    ('with_inner_vals', ('J_JOB1(a = "b", c=1 )', "J_JOB1", None)),
]


@pytest.mark.parametrize(["job_str", "job_name", "exception_str"],
                         [i[1] for i in job_name_parameters],
                         ids=[v[0] for v in job_name_parameters]
                         )
def test_job_name_parse(job_str, job_name, exception_str):
    # sourcery skip: no-conditionals-in-tests
    if exception_str:
        with pytest.raises(PyTaskforestParseException) as e:
            _ = Job.parse(job_str)
        assert e.value.message.startswith(exception_str)
    else:
        job = Job.parse(job_str)
        assert job.job_name == job_name


job_start_parameters = [
    ('simple', ('J_Job(start = "0230")', 2, 30, None)),
    ('two', ('J_Job(start = "26")', 2, 6, MSG_START_TIME_PARSING_FAILED)),
    ('three', ('J_Job(start = "206")', 2, 6, MSG_START_TIME_PARSING_FAILED)),
    ('None', ('J_Job()', None, None, None)),
    ('bad hh', ('J_Job(start = "a206")', None, None, MSG_START_TIME_PARSING_FAILED)),
    ('bad min', ('J_Job(start = "02a6")', None, None, MSG_START_TIME_PARSING_FAILED)),
]


@pytest.mark.parametrize(["job_str", "hh", "mm", "exception_str"],
                         [i[1] for i in job_start_parameters],
                         ids=[v[0] for v in job_start_parameters]
                         )
def test_job_start_parse(job_str, hh, mm, exception_str):
    # sourcery skip: no-conditionals-in-tests
    if exception_str:
        with pytest.raises(PyTaskforestParseException) as e:
            _ = Job.parse(job_str)
        assert e.value.message.startswith(exception_str)
    else:
        job = Job.parse(job_str)
        assert job.start_time_hr == hh
        assert job.start_time_min == mm
