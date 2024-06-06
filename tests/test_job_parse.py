import pytest

from app.model.job import Job
from app.model.exceptions import (
    PyTaskforestParseException,
    MSG_INNER_PARSING_FAILED,
    MSG_START_TIME_PARSING_FAILED,
    MSG_UNTIL_TIME_PARSING_FAILED,
    MSG_UNRECOGNIZED_PARAM,
    MSG_INVALID_TYPE,
)

job_name_parameters = [
    ('simple', ("J_Job()", "J_Job", None)),
    ('all_lower', ("j_job()", "j_job", None)),
    ('all_upper', ("J_JOB()", "J_JOB", None)),
    ('with_number', ("J_JOB1()", "J_JOB1", None)),
    ('start_with_number', ("1J_JOB1()", "1J_JOB1", None)),
    ('numbers_only', ("22()", "22", None)),
    ('with_inner_data', ("J_JOB1(sdfsdfd)", "J_JOB1__PARSE_FAIL", MSG_INNER_PARSING_FAILED)),
    ('with_inner_val', ('J_JOB1(a = "b" )', "J_JOB1", MSG_UNRECOGNIZED_PARAM)),
    ('with_inner_vals', ('J_JOB1(a = "b", c=1 )', "J_JOB1", MSG_UNRECOGNIZED_PARAM)),
    ('with_inner_vals', ('J_JOB1(tz="GMT")', "J_JOB1", None)),
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


job_until_parameters = [
    ('simple', ('J_Job(until = "0230")', 2, 30, None)),
    ('two', ('J_Job(until = "26")', 2, 6, MSG_UNTIL_TIME_PARSING_FAILED)),
    ('three', ('J_Job(until = "206")', 2, 6, MSG_UNTIL_TIME_PARSING_FAILED)),
    ('None', ('J_Job()', None, None, None)),
    ('bad hh', ('J_Job(until = "a206")', None, None, MSG_UNTIL_TIME_PARSING_FAILED)),
    ('bad min', ('J_Job(until = "02a6")', None, None, MSG_UNTIL_TIME_PARSING_FAILED)),
]


@pytest.mark.parametrize(["job_str", "hh", "mm", "exception_str"],
                         [i[1] for i in job_until_parameters],
                         ids=[v[0] for v in job_until_parameters]
                         )
def test_job_until_parse(job_str, hh, mm, exception_str):
    # sourcery skip: no-conditionals-in-tests
    if exception_str:
        with pytest.raises(PyTaskforestParseException) as e:
            _ = Job.parse(job_str)
        assert e.value.message.startswith(exception_str)
    else:
        job = Job.parse(job_str)
        assert job.until_hr == hh
        assert job.until_min == mm


job_invalid_parameters = [
    ('one good', ('J_Job(until = "0230", a=1)',)),
    ('two bad', ('J_Job(until = "0230", a=1, b=1)',)),
    ('zero good', ('J_Job(a=1)',)),
    ('all_bad', ('J_Job(a=1, b=1)',)),
]


@pytest.mark.parametrize(["job_str"],
                         [i[1] for i in job_invalid_parameters],
                         ids=[v[0] for v in job_invalid_parameters]
                         )
def test_job_invalid_parse(job_str):
    # sourcery skip: no-conditionals-in-tests
    with pytest.raises(PyTaskforestParseException) as e:
        _ = Job.parse(job_str)
    assert e.value.message.startswith(MSG_UNRECOGNIZED_PARAM)


job_invalid_type_parameters = [
    ('tz', ('J_Job(tz=1)', "J_Job/tz (1) is type int")),
    ('tz bool', ('J_Job(tz=true)', "J_Job/tz (True) is type bool")),
    ('tz bool', ('J_Job(tz=True)', "J_Job/tz (True) is type bool")),
    ('queue', ('J_Job(queue=2)', "J_Job/queue (2) is type int")),
    ('queue bool', ('J_Job(queue=false)', "J_Job/queue (False) is type bool")),
    ('queue bool', ('J_Job(queue=False)', "J_Job/queue (False) is type bool")),
]


@pytest.mark.parametrize(["job_str", "message_end"],
                         [i[1] for i in job_invalid_type_parameters],
                         ids=[v[0] for v in job_invalid_type_parameters]
                         )
def test_job_invalid_type(job_str, message_end):
    with pytest.raises(PyTaskforestParseException) as e:
        _ = Job.parse(job_str)
    assert e.value.message.startswith(MSG_INVALID_TYPE)
    assert e.value.message.endswith(message_end)
