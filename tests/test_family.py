import json
import os

import pytest

import pytf.dirs as dirs
import pytf.exceptions as ex
from pytf.dependency import (JobDependency, TimeDependency)
from pytf.forest import Forest
from pytf.family import Family, get_families_from_dir
from pytf.days import Days
from pytf.external_dependency import ExternalDependency
from pytf.calendar import Calendar
from pytf.job import Job
from pytf.mockdatetime import MockDateTime
from pytf.config import Config
from pytf.status import status


@pytest.fixture
def monday_config():
    return Config.from_str("""
    calendars.mondays = [
      "every Monday */*"
    ]
    """)


@pytest.fixture
def daily_config():
    return Config.from_str("""
    calendars.daily = [
      "*/*/*"
    ]
    """)


@pytest.fixture
def two_cal_config():
    return Config.from_str("""
    calendars.daily = [
      "*/*/*"
    ]
    calendars.mondays = [
      "every Monday */*"
    ]
    """)


@pytest.fixture
def two_cal_config_chicago():
    return Config.from_str("""
    calendars.daily = [
      "*/*/*"
    ]
    calendars.mondays = [
      "every Monday */*"
    ]
    primary_tz = "America/Chicago"
    """)


def test_family_split_single():
    line = " J()"
    jobs = Forest.split_jobs(line, "")
    assert (len(jobs) == 1)


def test_family_split_single_data():
    line = 'J(tz = "GMT", chained=FalSe)'
    jobs: [Job] = Forest.split_jobs(line, '')
    assert len(jobs) == 1
    assert jobs[0].job_name == 'J'
    assert jobs[0].chained is False
    assert jobs[0].tz == "GMT"


def test_family_split_double():
    line = 'J() E() # foo'
    jobs = Forest.split_jobs(line, '')
    assert (len(jobs) == 2)


def test_family_split_double_data():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert (len(jobs) == 2)

    assert jobs[0].job_name == 'J'
    assert jobs[0].tz == "GMT"
    assert jobs[0].chained is True

    assert jobs[1].job_name == 'E'
    assert jobs[1].chained is None
    assert jobs[1].tz == "America/Denver"


def test_family_line_one_success_cal(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert fam.name == "family"
    assert isinstance(fam.calendar_or_days, Calendar)
    assert fam.calendar_or_days.calendar_name == 'mondays'


def test_family_line_one_success_days(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c", days=["Mon", "Wed", "Fri"]

    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.name == "name"
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert len(fam.calendar_or_days.days) == 3
    assert 'Mon' in fam.calendar_or_days.days
    assert 'Wed' in fam.calendar_or_days.days
    assert 'Fri' in fam.calendar_or_days.days


def test_family_line_one_success_no_cal_days(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def test_full_family_line_one_forest(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2()
      J3()
    J4() J5()
    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 1
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[0].jobs[0]) == 2
    assert len(fam.forests[0].jobs[1]) == 1
    assert len(fam.forests[0].jobs[2]) == 2
    assert fam.forests[0].jobs[0][0].job_name == 'J1'
    assert fam.forests[0].jobs[0][0].family_name == 'name'
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'

    assert len(fam.jobs_by_name['J1'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J5'].dependencies)


def test_full_family_line_one_forest_plus_one_empty_unmet(two_cal_config, tmp_path):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    """
    two_cal_config.log_dir = tmp_path
    MockDateTime.set_mock(2024, 2, 14, 2, 13, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 1
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[0].jobs[0]) == 2
    assert len(fam.forests[0].jobs[1]) == 1
    assert len(fam.forests[0].jobs[2]) == 2
    assert fam.forests[0].jobs[0][0].job_name == 'J1'
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'

    assert len(fam.jobs_by_name['J1'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J3') in fam.jobs_by_name['J5'].dependencies)
    ready_job_names = fam.names_of_all_ready_jobs()
    assert not ready_job_names


def test_full_family_line_one_forest_plus_one_empty_met(two_cal_config, tmp_path):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    """
    MockDateTime.set_mock(2024, 2, 14, 2, 14, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 1
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[0].jobs[0]) == 2
    assert len(fam.forests[0].jobs[1]) == 1
    assert len(fam.forests[0].jobs[2]) == 2
    assert fam.forests[0].jobs[0][0].job_name == 'J1'
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'

    assert len(fam.jobs_by_name['J1'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'f1_name', 'J3') in fam.jobs_by_name['J5'].dependencies)

    ready_job_names = fam.names_of_all_ready_jobs()
    assert len(ready_job_names) == 2
    assert "J1" in ready_job_names
    assert "J2" in ready_job_names


def test_full_family_line_two_forests(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9()
    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 2
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[0].jobs[0]) == 2
    assert len(fam.forests[0].jobs[1]) == 1
    assert len(fam.forests[0].jobs[2]) == 2
    assert fam.forests[0].jobs[0][0].job_name == 'J1'
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert fam.forests[1].jobs[0][0].job_name == 'J6'
    assert fam.forests[1].jobs[0][1].job_name == 'J7'
    assert fam.forests[1].jobs[0][2].job_name == 'J8'
    assert fam.forests[1].jobs[0][3].job_name == 'J9'
    assert len(fam.jobs_by_name['J1'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J5'].dependencies)
    assert len(fam.jobs_by_name['J6'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J6'].dependencies)
    assert len(fam.jobs_by_name['J7'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J7'].dependencies)
    assert len(fam.jobs_by_name['J8'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J8'].dependencies)
    assert len(fam.jobs_by_name['J9'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J9'].dependencies)


def test_full_family_line_two_forests_with_one_empty_one(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    ---
    -----
    # foo
    J6()  J7() J8() J9()
    """
    fam = Family.parse("name", family_str, two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 2
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[0].jobs[0]) == 2
    assert len(fam.forests[0].jobs[1]) == 1
    assert len(fam.forests[0].jobs[2]) == 2
    assert fam.forests[0].jobs[0][0].job_name == 'J1'
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert fam.forests[1].jobs[0][0].job_name == 'J6'
    assert fam.forests[1].jobs[0][1].job_name == 'J7'
    assert fam.forests[1].jobs[0][2].job_name == 'J8'
    assert fam.forests[1].jobs[0][3].job_name == 'J9'
    assert len(fam.jobs_by_name['J1'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J5'].dependencies)
    assert len(fam.jobs_by_name['J6'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J6'].dependencies)
    assert len(fam.jobs_by_name['J7'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J7'].dependencies)
    assert len(fam.jobs_by_name['J8'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J8'].dependencies)
    assert len(fam.jobs_by_name['J9'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J9'].dependencies)


def test_full_family_line_three_forests(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9()
     - - - - - - - - -- ---- ------- - - - # ksdjflsdkjflsk
     J10()
    """
    fam = Family.parse("name", family_str, two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 3
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[0].jobs[0]) == 2
    assert len(fam.forests[0].jobs[1]) == 1
    assert len(fam.forests[0].jobs[2]) == 2
    assert fam.forests[0].jobs[0][0].job_name == 'J1'
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert fam.forests[1].jobs[0][0].job_name == 'J6'
    assert fam.forests[1].jobs[0][1].job_name == 'J7'
    assert fam.forests[1].jobs[0][2].job_name == 'J8'
    assert fam.forests[1].jobs[0][3].job_name == 'J9'
    assert len(fam.forests[2].jobs) == 1
    assert len(fam.forests[2].jobs[0]) == 1
    assert fam.forests[2].jobs[0][0].job_name == 'J10'
    assert len(fam.jobs_by_name['J1'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J5'].dependencies)
    assert len(fam.jobs_by_name['J6'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J6'].dependencies)
    assert len(fam.jobs_by_name['J7'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J7'].dependencies)
    assert len(fam.jobs_by_name['J8'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J8'].dependencies)
    assert len(fam.jobs_by_name['J9'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J9'].dependencies)
    assert len(fam.jobs_by_name['J10'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J10'].dependencies)


def test_external_deps(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    F2::JA()
    
    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9()
     - - - - - - - - -- ---- ------- - - - # ksdjflsdkjflsk
       F3::JB() F4::JC() 
     J10()
    """
    fam = Family.parse("name", family_str, two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 3
    assert len(fam.forests[0].jobs) == 4
    assert len(fam.forests[0].jobs[0]) == 1
    assert len(fam.forests[0].jobs[1]) == 2
    assert len(fam.forests[0].jobs[2]) == 1
    assert len(fam.forests[0].jobs[3]) == 2
    assert fam.forests[0].jobs[0][0].family_name == 'F2'
    assert fam.forests[0].jobs[0][0].job_name == 'JA'
    assert fam.forests[0].jobs[1][0].job_name == 'J1'
    assert fam.forests[0].jobs[1][1].job_name == 'J2'
    assert fam.forests[0].jobs[2][0].job_name == 'J3'
    assert fam.forests[0].jobs[3][0].job_name == 'J4'
    assert fam.forests[0].jobs[3][1].job_name == 'J5'
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert fam.forests[1].jobs[0][0].job_name == 'J6'
    assert fam.forests[1].jobs[0][1].job_name == 'J7'
    assert fam.forests[1].jobs[0][2].job_name == 'J8'
    assert fam.forests[1].jobs[0][3].job_name == 'J9'
    assert len(fam.forests[2].jobs) == 2
    assert len(fam.forests[2].jobs[0]) == 2
    assert len(fam.forests[2].jobs[1]) == 1
    assert fam.forests[2].jobs[0][0].family_name == 'F3'
    assert fam.forests[2].jobs[0][0].job_name == 'JB'
    assert fam.forests[2].jobs[0][1].family_name == 'F4'
    assert fam.forests[2].jobs[0][1].job_name == 'JC'
    assert fam.forests[2].jobs[1][0].job_name == 'J10'
    assert len(fam.jobs_by_name['J1'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert (ExternalDependency('F2', 'JA') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert (ExternalDependency('F2', 'JA') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J5'].dependencies)
    assert len(fam.jobs_by_name['J6'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J6'].dependencies)
    assert len(fam.jobs_by_name['J7'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J7'].dependencies)
    assert len(fam.jobs_by_name['J8'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J8'].dependencies)
    assert len(fam.jobs_by_name['J9'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J9'].dependencies)
    assert len(fam.jobs_by_name['J10'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J10'].dependencies)
    assert (ExternalDependency('F3', 'JB') in fam.jobs_by_name['J10'].dependencies)
    assert (ExternalDependency('F4', 'JC') in fam.jobs_by_name['J10'].dependencies)


def test_external_deps_tz(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    F2::JA()
    
    J1(start="0330") J2(start="0430", tz="America/Denver") # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9()
     - - - - - - - - -- ---- ------- - - - # ksdjflsdkjflsk
       F3::JB() F4::JC() 
     J10()
    """
    fam = Family.parse("name", family_str, two_cal_config)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 3
    assert len(fam.forests[0].jobs) == 4
    assert len(fam.forests[0].jobs[0]) == 1
    assert len(fam.forests[0].jobs[1]) == 2
    assert len(fam.forests[0].jobs[2]) == 1
    assert len(fam.forests[0].jobs[3]) == 2
    assert fam.forests[0].jobs[0][0].family_name == 'F2'
    assert fam.forests[0].jobs[0][0].job_name == 'JA'
    assert fam.forests[0].jobs[1][0].job_name == 'J1'
    assert fam.forests[0].jobs[1][1].job_name == 'J2'
    assert fam.forests[0].jobs[2][0].job_name == 'J3'
    assert fam.forests[0].jobs[3][0].job_name == 'J4'
    assert fam.forests[0].jobs[3][1].job_name == 'J5'
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert fam.forests[1].jobs[0][0].job_name == 'J6'
    assert fam.forests[1].jobs[0][1].job_name == 'J7'
    assert fam.forests[1].jobs[0][2].job_name == 'J8'
    assert fam.forests[1].jobs[0][3].job_name == 'J9'
    assert len(fam.forests[2].jobs) == 2
    assert len(fam.forests[2].jobs[0]) == 2
    assert len(fam.forests[2].jobs[1]) == 1
    assert fam.forests[2].jobs[0][0].family_name == 'F3'
    assert fam.forests[2].jobs[0][0].job_name == 'JB'
    assert fam.forests[2].jobs[0][1].family_name == 'F4'
    assert fam.forests[2].jobs[0][1].job_name == 'JC'
    assert fam.forests[2].jobs[1][0].job_name == 'J10'
    assert len(fam.jobs_by_name['J1'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert (TimeDependency(two_cal_config, 3, 30, 'GMT') in fam.jobs_by_name['J1'].dependencies)
    assert (ExternalDependency('F2', 'JA') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J2'].dependencies)
    assert (TimeDependency(two_cal_config, 4, 30, 'America/Denver') in fam.jobs_by_name['J2'].dependencies)
    assert (ExternalDependency('F2', 'JA') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config, 'name', 'J3') in fam.jobs_by_name['J5'].dependencies)
    assert len(fam.jobs_by_name['J6'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J6'].dependencies)
    assert len(fam.jobs_by_name['J7'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J7'].dependencies)
    assert len(fam.jobs_by_name['J8'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J8'].dependencies)
    assert len(fam.jobs_by_name['J9'].dependencies) == 1
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J9'].dependencies)
    assert len(fam.jobs_by_name['J10'].dependencies) == 3
    assert (TimeDependency(two_cal_config, 2, 14, 'GMT') in fam.jobs_by_name['J10'].dependencies)
    assert (ExternalDependency('F3', 'JB') in fam.jobs_by_name['J10'].dependencies)
    assert (ExternalDependency('F4', 'JC') in fam.jobs_by_name['J10'].dependencies)


def test_external_deps_fallback_tz(two_cal_config_chicago, tmp_path):
    family_str = """start="0214", queue="main", email="a@b.c"

    F2::JA()
    
    J1(start="0330") J2(start="0430", tz="America/Denver") # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9()
     - - - - - - - - -- ---- ------- - - - # ksdjflsdkjflsk
       F3::JB() F4::JC() 
     J10()
    """

    MockDateTime.set_mock(2024, 2, 14, 2, 14, 0, 'America/Chicago')
    two_cal_config_chicago.log_dir = os.path.join(tmp_path, 'log_dir')
    two_cal_config_chicago.family_dir = os.path.join(tmp_path, 'family_dir')
    dated_family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now(tz="America/Chicago"))
    dirs.make_dir(dated_family_dir)
    with open(os.path.join(dated_family_dir, "F1"), "w") as f:
        f.write(family_str)
    with open(os.path.join(dated_family_dir, "F2"), "w") as f:
        f.write("""start="0200", queue="main", email="a@b.c"
        JA()
        """)
    with open(os.path.join(dated_family_dir, "F3"), "w") as f:
        f.write("""start="0200", queue="main", email="a@b.c"
        JB()
        """)
    with open(os.path.join(dated_family_dir, "F4"), "w") as f:
        f.write("""start="0200", queue="main", email="a@b.c"
        JC()
        """)
    todays_log_dir = dirs.todays_log_dir(two_cal_config_chicago)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("F1", family_str, two_cal_config_chicago)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz is None
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert len(fam.forests) == 3
    assert len(fam.forests[0].jobs) == 4
    assert len(fam.forests[0].jobs[0]) == 1
    assert len(fam.forests[0].jobs[1]) == 2
    assert len(fam.forests[0].jobs[2]) == 1
    assert len(fam.forests[0].jobs[3]) == 2
    assert fam.forests[0].jobs[0][0].family_name == 'F2'
    assert fam.forests[0].jobs[0][0].job_name == 'JA'
    assert fam.forests[0].jobs[1][0].job_name == 'J1'
    assert fam.forests[0].jobs[1][1].job_name == 'J2'
    assert fam.forests[0].jobs[2][0].job_name == 'J3'
    assert fam.forests[0].jobs[3][0].job_name == 'J4'
    assert fam.forests[0].jobs[3][1].job_name == 'J5'
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert fam.forests[1].jobs[0][0].job_name == 'J6'
    assert fam.forests[1].jobs[0][1].job_name == 'J7'
    assert fam.forests[1].jobs[0][2].job_name == 'J8'
    assert fam.forests[1].jobs[0][3].job_name == 'J9'
    assert len(fam.forests[2].jobs) == 2
    assert len(fam.forests[2].jobs[0]) == 2
    assert len(fam.forests[2].jobs[1]) == 1
    assert fam.forests[2].jobs[0][0].family_name == 'F3'
    assert fam.forests[2].jobs[0][0].job_name == 'JB'
    assert fam.forests[2].jobs[0][1].family_name == 'F4'
    assert fam.forests[2].jobs[0][1].job_name == 'JC'
    assert fam.forests[2].jobs[1][0].job_name == 'J10'
    assert len(fam.jobs_by_name['J1'].dependencies) == 3
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J1'].dependencies)
    assert (TimeDependency(two_cal_config_chicago, 3, 30, 'America/Chicago') in fam.jobs_by_name['J1'].dependencies)
    assert (ExternalDependency('F2', 'JA') in fam.jobs_by_name['J1'].dependencies)
    assert len(fam.jobs_by_name['J2'].dependencies) == 3
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J2'].dependencies)
    assert (TimeDependency(two_cal_config_chicago, 4, 30, 'America/Denver') in fam.jobs_by_name['J2'].dependencies)
    assert (ExternalDependency('F2', 'JA') in fam.jobs_by_name['J2'].dependencies)
    assert len(fam.jobs_by_name['J3'].dependencies) == 3
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config_chicago, 'F1', 'J1') in fam.jobs_by_name['J3'].dependencies)
    assert (JobDependency(two_cal_config_chicago, 'F1', 'J2') in fam.jobs_by_name['J3'].dependencies)
    assert len(fam.jobs_by_name['J4'].dependencies) == 2
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J4'].dependencies)
    assert (JobDependency(two_cal_config_chicago, 'F1', 'J3') in fam.jobs_by_name['J4'].dependencies)
    assert len(fam.jobs_by_name['J5'].dependencies) == 2
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J5'].dependencies)
    assert (JobDependency(two_cal_config_chicago, 'F1', 'J3') in fam.jobs_by_name['J5'].dependencies)
    assert len(fam.jobs_by_name['J6'].dependencies) == 1
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J6'].dependencies)
    assert len(fam.jobs_by_name['J7'].dependencies) == 1
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J7'].dependencies)
    assert len(fam.jobs_by_name['J8'].dependencies) == 1
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J8'].dependencies)
    assert len(fam.jobs_by_name['J9'].dependencies) == 1
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J9'].dependencies)
    assert len(fam.jobs_by_name['J10'].dependencies) == 3
    assert (TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago') in fam.jobs_by_name['J10'].dependencies)
    assert (ExternalDependency('F3', 'JB') in fam.jobs_by_name['J10'].dependencies)
    assert (ExternalDependency('F4', 'JC') in fam.jobs_by_name['J10'].dependencies)

    status_json = status(two_cal_config_chicago)
    assert len(status_json['status']['flat_list']) == 13
    assert status_json['status']['flat_list'][0]['job_name'] == 'J1'
    assert status_json['status']['flat_list'][0]['family_name'] == 'F1'
    assert status_json['status']['flat_list'][1]['job_name'] == 'J10'
    assert status_json['status']['flat_list'][2]['job_name'] == 'J2'
    assert status_json['status']['flat_list'][3]['job_name'] == 'J3'
    assert status_json['status']['flat_list'][4]['job_name'] == 'J4'
    assert status_json['status']['flat_list'][5]['job_name'] == 'J5'
    assert status_json['status']['flat_list'][6]['job_name'] == 'J6'
    assert status_json['status']['flat_list'][7]['job_name'] == 'J7'
    assert status_json['status']['flat_list'][8]['job_name'] == 'J8'
    assert status_json['status']['flat_list'][9]['job_name'] == 'J9'
    


    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 4
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)
    assert (all_families[0].name == 'F1')
    assert (all_families[1].name == 'F2')
    assert (all_families[2].name == 'F3')
    assert (all_families[3].name == 'F4')
    assert ('JA' in all_families[1].names_of_all_ready_jobs())
    assert ('JB' in all_families[2].names_of_all_ready_jobs())
    assert ('JC' in all_families[3].names_of_all_ready_jobs())


    # show that ext dep is not enough if a time dep exists
    with open(os.path.join(todays_log_dir, "F2.JA.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F2"\n')
        f.write('job_name = "JA"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    status_json = status(two_cal_config_chicago)
    assert len(status_json['status']['flat_list']) == 13

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)
    assert (not all_families[1].names_of_all_ready_jobs())
    assert ('JB' in all_families[2].names_of_all_ready_jobs())
    assert ('JC' in all_families[3].names_of_all_ready_jobs())


    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 4
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs

    # 2 other ext deps
    with open(os.path.join(todays_log_dir, "F3.JB.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F3"\n')
        f.write('job_name = "JB"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    with open(os.path.join(todays_log_dir, "F4.JC.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F4"\n')
        f.write('job_name = "JC"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 5
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs
    assert "J10" in ready_jobs

    status_json = status(two_cal_config_chicago)
    assert len(status_json['status']['flat_list']) == 13

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)
    assert (not all_families[1].names_of_all_ready_jobs())
    assert (not all_families[2].names_of_all_ready_jobs())
    assert (not all_families[3].names_of_all_ready_jobs())

    MockDateTime.set_mock(2024, 2, 14, 3, 30, 0, 'America/Chicago')
    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 6
    assert "J1" in ready_jobs
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs
    assert "J10" in ready_jobs

    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 7
    assert "J1" in ready_jobs
    assert "J2" in ready_jobs
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs
    assert "J10" in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J1.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J1"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    with open(os.path.join(todays_log_dir, "name.J2.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J2"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 6
    assert "J3" in ready_jobs
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs
    assert "J10" in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J3.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J3"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 7
    assert "J4" in ready_jobs
    assert "J5" in ready_jobs
    assert "J6" in ready_jobs
    assert "J7" in ready_jobs
    assert "J8" in ready_jobs
    assert "J9" in ready_jobs
    assert "J10" in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J4.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J4"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 6
    assert 'J4' not in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J5.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J5"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 5
    assert 'J5' not in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J6.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J6"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 4
    assert 'J6' not in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J7.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J7"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 3
    assert 'J7' not in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J8.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J8"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 2
    assert 'J8' not in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J9.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J9"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 1
    assert 'J9' not in ready_jobs

    with open(os.path.join(todays_log_dir, "name.J10.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "F1"\n')
        f.write('job_name = "J10"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
        f.write('error_code = 0\n')

    ready_jobs = fam.names_of_all_ready_jobs()
    assert len(ready_jobs) == 0


def test_duplicate_jobs(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    F2::JA()
    
    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9() J2()
     - - - - - - - - -- ---- ------- - - - # ksdjflsdkjflsk
       F3::JB() F4::JC() 
     J10()
    """
    with pytest.raises(ex.PyTaskforestParseException) as excinfo:
        _ = Family.parse("name", family_str, two_cal_config)
    assert str(excinfo.value) == f"{ex.MSG_FAMILY_JOB_TWICE} name::J2"
