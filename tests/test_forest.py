import pytest

from app.model.forest import Forest
from app.model.job import Job


def test_family_split_single():
    line = " J()"
    jobs = Forest.split_jobs(line)
    assert(len(jobs) == 1)


def test_family_split_single_data():
    line = 'J(tz = "GMT", chained=FalSe)'
    jobs: [Job] = Forest.split_jobs(line)
    assert len(jobs) == 1
    assert jobs[0].job_name == 'J'
    assert jobs[0].chained is False
    assert jobs[0].tz == "GMT"


def test_family_split_double():
    line = 'J() E() # foo'
    jobs = Forest.split_jobs(line)
    assert(len(jobs) == 2)


def test_family_split_double_data():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line)
    assert(len(jobs) == 2)

    assert jobs[0].job_name == 'J'
    assert jobs[0].tz == "GMT"
    assert jobs[0].chained is True

    assert jobs[1].job_name == 'E'
    assert jobs[1].chained is None
    assert jobs[1].tz == "America/Denver"

