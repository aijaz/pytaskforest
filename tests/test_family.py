import os
import pathlib

import pytest
import tomlkit

import pytf.dirs as dirs
import pytf.exceptions as ex
from pytf.dependency import (JobDependency, TimeDependency)
from pytf.forest import Forest
from pytf.family import Family, get_families_from_dir
from pytf.days import Days
from pytf.external_dependency import ExternalDependency
from pytf.pytf_calendar import Calendar
from pytf.job import Job
from pytf.mockdatetime import MockDateTime
from pytf.config import Config
from pytf.status import status
from pytf.mark import mark
from pytf.holdAndRelease import (hold, remove_hold, release_dependencies)


@pytest.fixture
def three_forest_family():
    return """start="0214", tz = "GMT", queue="main", email="a@b.c"

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


@pytest.fixture
def family_two_forests():
    return """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    J6()  J7() J8() J9()
    """


@pytest.fixture
def single_forest_family():
    return """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2()
      J3()
    J4() J5()
    """


@pytest.fixture
def f1_name_family_str():
    return """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    """


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
def denver_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
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


def test_family_split_single_data_job_num():
    line = 'J(tz = "GMT", chained=False)'
    jobs: [Job] = Forest.split_jobs(line, '')
    assert len(jobs) == 1


def test_family_split_single_data_job_name():
    line = 'J(tz = "GMT", chained=False)'
    jobs: [Job] = Forest.split_jobs(line, '')
    assert jobs[0].job_name == 'J'


def test_family_split_single_data_chained():
    line = 'J(tz = "GMT", chained=False)'
    jobs: [Job] = Forest.split_jobs(line, '')
    assert jobs[0].chained is False


def test_family_split_single_data_chained_case():
    line = 'J(tz = "GMT", chained=FaLsE)'
    jobs: [Job] = Forest.split_jobs(line, '')
    assert jobs[0].chained is False


def test_family_split_single_data_tz():
    line = 'J(tz = "GMT", chained=FalSe)'
    jobs: [Job] = Forest.split_jobs(line, '')
    assert jobs[0].tz == "GMT"


def test_family_split_double():
    line = 'J() E() # foo'
    jobs = Forest.split_jobs(line, '')
    assert (len(jobs) == 2)


def test_family_split_double_data_num_jobs():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert (len(jobs) == 2)


def test_family_split_double_data_job_0_name():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert jobs[0].job_name == 'J'


def test_family_split_double_data_job_0_tz():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert jobs[0].tz == "GMT"


def test_family_split_double_data_job_0_chained():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert jobs[0].chained is True


def test_family_split_double_data_job_1_name():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert jobs[1].job_name == 'E'


def test_family_split_double_data_job_1_tz():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert jobs[1].tz == "America/Denver"


def test_family_split_double_data_job_1_chained():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line, '')
    assert jobs[1].chained is None


def test_split_jobs_non_repeat():
    line = "J6()  J7() J8() J9() J2()"
    jobs = Forest.split_jobs(line, '')
    assert [j.job_name for j in jobs] == ['J6', 'J7', 'J8', 'J9', 'J2']


def test_split_jobs_repeat():
    line = "J6(every=900)  J7() J8() J9() J2()"
    jobs = Forest.split_jobs(line, '')
    assert [j.job_name for j in jobs] == ['J6', 'J7', 'J8', 'J9', 'J2']


def test_family_line_one_success_cal_start_time_parse_hour(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert fam.start_time_hr == 2


def test_family_line_one_success_cal_start_time_parse_min(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert fam.start_time_min == 14


def test_family_line_one_success_cal_general_toml(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'


def test_family_line_one_success_cal_family_name(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert fam.name == "family"


def test_family_line_one_success_cal_calendar_days_type(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert isinstance(fam.calendar_or_days, Calendar)


def test_family_line_one_success_cal_calendary_name(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=two_cal_config)
    assert fam.calendar_or_days.calendar_name == 'mondays'


def test_family_line_one_success_days_type(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c", days=["Mon", "Wed", "Fri"]

    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert isinstance(fam.calendar_or_days, Days)
    assert len(fam.calendar_or_days.days) == 3
    assert 'Mon' in fam.calendar_or_days.days
    assert 'Wed' in fam.calendar_or_days.days
    assert 'Fri' in fam.calendar_or_days.days


def test_family_line_one_success_days_contents(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c", days=["Mon", "Wed", "Fri"]

    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert fam.calendar_or_days.days == ['Mon', 'Wed', 'Fri']


def test_family_line_one_success_no_cal_days_type(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert isinstance(fam.calendar_or_days, Days)


def test_family_line_one_success_no_cal_days_days(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    """
    fam = Family.parse("name", family_str, config=two_cal_config)
    assert fam.calendar_or_days.days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def test_full_family_line_one_forest_name(two_cal_config, single_forest_family):
    fam = Family.parse("single_forest_family", single_forest_family, config=two_cal_config)
    assert fam.forests[0].jobs[0][0].family_name == 'single_forest_family'


def test_full_family_line_one_forest_num_forests(two_cal_config, single_forest_family):
    fam = Family.parse("single_forest_family", single_forest_family, config=two_cal_config)
    assert len(fam.forests) == 1


def test_full_family_line_one_forest_num_forest_lines(two_cal_config, single_forest_family):
    fam = Family.parse("single_forest_family", single_forest_family, config=two_cal_config)
    assert len(fam.forests[0].jobs) == 3


def test_full_family_line_one_forest_jobs(two_cal_config, single_forest_family):
    fam = Family.parse("single_forest_family", single_forest_family, config=two_cal_config)
    assert [x.job_name for x in fam.forests[0].jobs[0]] == ['J1', 'J2']
    assert [x.job_name for x in fam.forests[0].jobs[1]] == ['J3']
    assert [x.job_name for x in fam.forests[0].jobs[2]] == ['J4', 'J5']


def test_full_family_line_one_forest_dependencies(two_cal_config, single_forest_family):
    fam = Family.parse("single_forest_family", single_forest_family, config=two_cal_config)

    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J3'].dependencies == {
        TimeDependency(two_cal_config, 2, 14, 'GMT'),
        JobDependency(two_cal_config, 'single_forest_family', 'J1'),
        JobDependency(two_cal_config, 'single_forest_family', 'J2')
    }
    assert fam.jobs_by_name['J4'].dependencies == {
        TimeDependency(two_cal_config, 2, 14, 'GMT'),
        JobDependency(two_cal_config, 'single_forest_family', 'J3'),
    }
    assert fam.jobs_by_name['J5'].dependencies == {
        TimeDependency(two_cal_config, 2, 14, 'GMT'),
        JobDependency(two_cal_config, 'single_forest_family', 'J3'),
    }


def test_full_family_line_one_forest_plus_one_empty_unmet_forests(two_cal_config, tmp_path, f1_name_family_str):
    two_cal_config.log_dir = tmp_path
    MockDateTime.set_mock(2024, 2, 14, 2, 13, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", f1_name_family_str, config=two_cal_config)

    assert len(fam.forests) == 1


def test_full_family_line_one_forest_plus_one_empty_unmet_jobs(two_cal_config, tmp_path, f1_name_family_str):
    two_cal_config.log_dir = tmp_path
    MockDateTime.set_mock(2024, 2, 14, 2, 13, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", f1_name_family_str, config=two_cal_config)

    assert [x.job_name for x in fam.forests[0].jobs[0]] == ['J1', 'J2']
    assert [x.job_name for x in fam.forests[0].jobs[1]] == ['J3']
    assert [x.job_name for x in fam.forests[0].jobs[2]] == ['J4', 'J5']


def test_full_family_line_one_forest_plus_one_empty_unmet_dependencies(two_cal_config, tmp_path, f1_name_family_str):
    two_cal_config.log_dir = tmp_path
    MockDateTime.set_mock(2024, 2, 14, 2, 13, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", f1_name_family_str, config=two_cal_config)

    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J3'].dependencies == {
        TimeDependency(two_cal_config, 2, 14, 'GMT'),
        JobDependency(two_cal_config, 'f1_name', 'J1'),
        JobDependency(two_cal_config, 'f1_name', 'J2')
    }
    assert fam.jobs_by_name['J4'].dependencies == {
        TimeDependency(two_cal_config, 2, 14, 'GMT'),
        JobDependency(two_cal_config, 'f1_name', 'J3'),
    }
    assert fam.jobs_by_name['J5'].dependencies == {
        TimeDependency(two_cal_config, 2, 14, 'GMT'),
        JobDependency(two_cal_config, 'f1_name', 'J3'),
    }


def test_full_family_line_one_forest_plus_one_empty_unmet_nothing_ready(two_cal_config, tmp_path, f1_name_family_str):
    two_cal_config.log_dir = tmp_path
    MockDateTime.set_mock(2024, 2, 14, 2, 13, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", f1_name_family_str, config=two_cal_config)
    ready_job_names = fam.names_of_all_ready_jobs()
    assert not ready_job_names


def test_full_family_line_one_forest_plus_one_empty_met_ready(two_cal_config, tmp_path, f1_name_family_str):
    MockDateTime.set_mock(2024, 2, 14, 2, 14, 0, 'GMT')
    two_cal_config.log_dir = tmp_path
    todays_log_dir = dirs.todays_log_dir(two_cal_config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("f1_name", f1_name_family_str, config=two_cal_config)

    ready_job_names = fam.names_of_all_ready_jobs()
    assert ready_job_names == ["J1", "J2"]


def test_full_family_line_two_forests_forests(two_cal_config, family_two_forests):
    fam = Family.parse("name", family_two_forests, config=two_cal_config)
    assert len(fam.forests) == 2


def test_full_family_line_two_forests_job_lines(two_cal_config, family_two_forests):
    fam = Family.parse("name", family_two_forests, config=two_cal_config)
    assert len(fam.forests[0].jobs) == 3
    assert len(fam.forests[1].jobs) == 1


def test_full_family_line_two_forests_jobs(two_cal_config, family_two_forests):
    fam = Family.parse("name", family_two_forests, config=two_cal_config)
    assert [x.job_name for x in fam.forests[0].jobs[0]] == ['J1', 'J2']
    assert [x.job_name for x in fam.forests[0].jobs[1]] == ['J3']
    assert [x.job_name for x in fam.forests[0].jobs[2]] == ['J4', 'J5']
    assert [x.job_name for x in fam.forests[1].jobs[0]] == ['J6', 'J7', 'J8', 'J9']


def test_full_family_line_two_forests_dependencies(two_cal_config, family_two_forests):
    fam = Family.parse("name", family_two_forests, config=two_cal_config)
    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J3'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J1'),
                                                   JobDependency(two_cal_config, 'name', 'J2')}
    assert fam.jobs_by_name['J4'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J5'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J6'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J7'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J8'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J9'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}


def test_full_family_line_two_forests_with_empty_ones_num_forests(two_cal_config):
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
    assert len(fam.forests) == 2


def test_full_family_line_two_forests_with_empty_ones_jobs(two_cal_config):
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
    assert len(fam.forests[1].jobs) == 1
    assert len(fam.forests[1].jobs[0]) == 4
    assert [x.job_name for x in fam.forests[1].jobs[0]] == ['J6', 'J7', 'J8', 'J9']


def test_full_family_line_three_forests_num_families(two_cal_config):
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
    assert len(fam.forests) == 3


def test_full_family_line_three_forests_jobs(two_cal_config):
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
    assert len(fam.forests[1].jobs[0]) == 4
    assert len(fam.forests[2].jobs) == 1

    assert [x.job_name for x in fam.forests[1].jobs[0]] == ['J6', 'J7', 'J8', 'J9']
    assert [x.job_name for x in fam.forests[2].jobs[0]] == ['J10']


def test_full_family_line_three_forests_dependencies(two_cal_config):
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

    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J3'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J1'),
                                                   JobDependency(two_cal_config, 'name', 'J2')}
    assert fam.jobs_by_name['J4'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J5'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J6'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J7'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J8'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J9'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J10'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}


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
    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   ExternalDependency('F2', 'JA')
                                                   }
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   ExternalDependency('F2', 'JA'),
                                                   }
    assert fam.jobs_by_name['J3'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J1'),
                                                   JobDependency(two_cal_config, 'name', 'J2')}
    assert fam.jobs_by_name['J4'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J5'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J6'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J7'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J8'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J9'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J10'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                    ExternalDependency('F3', 'JB'),
                                                    ExternalDependency('F4', 'JC'),
                                                    }


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
    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   ExternalDependency('F2', 'JA'),
                                                   TimeDependency(two_cal_config, 3, 30, 'GMT'),
                                                   }
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   ExternalDependency('F2', 'JA'),
                                                   TimeDependency(two_cal_config, 4, 30, 'America/Denver'),
                                                   }
    assert fam.jobs_by_name['J3'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J1'),
                                                   JobDependency(two_cal_config, 'name', 'J2')}
    assert fam.jobs_by_name['J4'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J5'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                   JobDependency(two_cal_config, 'name', 'J3')}
    assert fam.jobs_by_name['J6'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J7'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J8'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J9'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT')}
    assert fam.jobs_by_name['J10'].dependencies == {TimeDependency(two_cal_config, 2, 14, 'GMT'),
                                                    ExternalDependency('F3', 'JB'),
                                                    ExternalDependency('F4', 'JC'),
                                                    }


def test_external_deps_fallback_tz_dependencies(two_cal_config_chicago, tmp_path):
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
     J99()
    """

    fam = Family.parse("F1", family_str, two_cal_config_chicago)
    MockDateTime.set_mock(2024, 2, 14, 2, 14, 0, 'America/Chicago')

    assert fam.jobs_by_name['J1'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago'),
                                                   ExternalDependency('F2', 'JA'),
                                                   TimeDependency(two_cal_config_chicago, 3, 30, 'America/Chicago'),
                                                   }
    assert fam.jobs_by_name['J2'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago'),
                                                   ExternalDependency('F2', 'JA'),
                                                   TimeDependency(two_cal_config_chicago, 4, 30, 'America/Denver'),
                                                   }
    assert fam.jobs_by_name['J3'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago'),
                                                   JobDependency(two_cal_config_chicago, 'F1', 'J1'),
                                                   JobDependency(two_cal_config_chicago, 'F1', 'J2')}
    assert fam.jobs_by_name['J4'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago'),
                                                   JobDependency(two_cal_config_chicago, 'F1', 'J3')}
    assert fam.jobs_by_name['J5'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago'),
                                                   JobDependency(two_cal_config_chicago, 'F1', 'J3')}
    assert fam.jobs_by_name['J6'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago')}
    assert fam.jobs_by_name['J7'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago')}
    assert fam.jobs_by_name['J8'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago')}
    assert fam.jobs_by_name['J9'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago')}
    assert fam.jobs_by_name['J99'].dependencies == {TimeDependency(two_cal_config_chicago, 2, 14, 'America/Chicago'),
                                                    ExternalDependency('F3', 'JB'),
                                                    ExternalDependency('F4', 'JC'),
                                                    }


def test_external_deps_fallback_tz_status_jobs(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    status_json = status(two_cal_config_chicago)
    assert [f"{j['family_name']}{j['job_name']}" for j in status_json['status']['flat_list']] == [
        "F1J1", "F1J2", "F1J3", "F1J4", "F1J5", "F1J6", "F1J7", "F1J8", "F1J9", "F1J99", "F2JA", "F3JB", "F4JC"
    ]


def test_external_deps_fallback_tz_status_1(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Ready', 'Ready', 'Ready',
    ]


def test_external_deps_fallback_tz_status_ready_jobs(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    assert fam.names_of_all_ready_jobs() == ["J6", "J7", "J8", "J9"]


def test_external_deps_fallback_tz_status_names_of_ready_jobs_all_families(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)
    assert [f.name for f in all_families] == ['F1', 'F2', 'F3', 'F4']


def test_external_deps_fallback_tz_status_names_of_ready_jobs_external_deps(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)
    assert ('JA' in all_families[1].names_of_all_ready_jobs())
    assert ('JB' in all_families[2].names_of_all_ready_jobs())
    assert ('JC' in all_families[3].names_of_all_ready_jobs())


def test_external_deps_not_enough_if_time_dep_exists(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Success', 'Ready', 'Ready',
    ]


def create_job_done_file(d, fn, jn, tz, q, w, st, ec):
    file_name = f"{fn}.{jn}.{q}.{w}.{st}.info"
    with open(os.path.join(d, file_name), "w") as f:
        f.write(f'family_name = "{fn}"\n')
        f.write(f'job_name = "{jn}"\n')
        f.write(f'tz = "{tz}"\n')
        f.write(f'queue_name = "{q}"\n')
        f.write(f'worker_name = "{w}"\n')
        f.write('start_time = "{st}"\n')
        f.write(f'error_code = {ec}\n')
    return file_name


def create_job_running_file(d, fn, jn, tz, q, w, st, ec):
    file_name = f"{fn}.{jn}.{q}.{w}.{st}.info"
    with open(os.path.join(d, file_name), "w") as f:
        f.write(f'family_name = "{fn}"\n')
        f.write(f'job_name = "{jn}"\n')
        f.write(f'tz = "{tz}"\n')
        f.write(f'queue_name = "{q}"\n')
        f.write(f'worker_name = "{w}"\n')
        f.write('start_time = "{st}"\n')
    return file_name


def test_all_ready_jobs_modified_as_jobs_complete(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)

    assert all_families[0].names_of_all_ready_jobs() == ['J6', 'J7', 'J8', 'J9']
    assert not all_families[1].names_of_all_ready_jobs()
    assert all_families[2].names_of_all_ready_jobs() == ['JB']
    assert all_families[3].names_of_all_ready_jobs() == ['JC']


def test_two_more_ext_deps_ready_jobs(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    family_dir = dirs.dated_subdir(two_cal_config_chicago.family_dir, MockDateTime.now('America/Chicago'))
    all_families = get_families_from_dir(family_dir, two_cal_config_chicago)

    assert all_families[0].names_of_all_ready_jobs() == ['J6', 'J7', 'J8', 'J9', 'J99']
    assert not all_families[1].names_of_all_ready_jobs()
    assert not all_families[1].names_of_all_ready_jobs()
    assert not all_families[1].names_of_all_ready_jobs()


def test_two_more_ext_deps_status(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_3_30_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 3, 30, 0, 'America/Chicago')
    assert fam.names_of_all_ready_jobs() == ['J1', 'J6', 'J7', 'J8', 'J9', 'J99']


def test_3_30_status(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 3, 30, 0, 'America/Chicago')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Ready', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_3_31_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    assert fam.names_of_all_ready_jobs() == ['J1', 'J2', 'J6', 'J7', 'J8', 'J9', 'J99']


def test_3_31_status(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Ready', 'Ready', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_post_j1_j2_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J3', 'J6', 'J7', 'J8', 'J9', 'J99']


def test_post_j3_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J99']


def test_post_j4_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J5', 'J6', 'J7', 'J8', 'J9', 'J99']


def test_post_j5_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J6', 'J7', 'J8', 'J9', 'J99']


def test_post_j6_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J7', 'J8', 'J9', 'J99']


def test_post_j7_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J7', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J8', 'J9', 'J99']


def test_post_j8_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J7', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J8', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J9', 'J99']


def test_post_j9_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J7', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J8', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J9', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert fam.names_of_all_ready_jobs() == ['J99']


def test_mark_jc_failed_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J7', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J8', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J9', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 127)
    assert not fam.names_of_all_ready_jobs()


def test_mark_jc_failed_status(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J7', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J8', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J9', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 127)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Success', 'Success', 'Success', 'Success', 'Success',
        'Success', 'Success', 'Success', 'Success', 'Waiting',
        'Success', 'Success', 'Failure',
    ]


def test_j99_success_ready(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 4, 31, 0, 'America/Denver')
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J3', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J4', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J5', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J6', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J7', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J8', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F1', 'J9', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 127)
    create_job_done_file(todays_log_dir, 'F1', 'J99', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    assert not fam.names_of_all_ready_jobs()


def prep_status_family(tmp_path, two_cal_config_chicago):
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
     J99()
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
    return fam, todays_log_dir


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
     J99()
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("name", family_str, two_cal_config)
    assert str(exc_info.value) == f"{ex.MSG_FAMILY_JOB_TWICE} name::J2"


def prep_repeat_family(path, config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="0330", every=1800, until="0500")
    """
    MockDateTime.set_mock(2024, 3, 29, 2, 14, 0, 'America/Denver')
    config.log_dir = os.path.join(path, 'log_dir')
    config.family_dir = os.path.join(path, 'family_dir')
    dated_family_dir = dirs.dated_subdir(config.family_dir, MockDateTime.now(tz="America/Denver"))
    dirs.make_dir(dated_family_dir)
    with open(os.path.join(dated_family_dir, "F1"), "w") as f:
        f.write(family_str)

    todays_log_dir = dirs.todays_log_dir(config)
    dirs.make_dir(todays_log_dir)
    fam = Family.parse("F1", family_str, config)
    return fam, todays_log_dir


def test_repeat_job_creation(tmp_path, denver_config):
    prep_repeat_family(tmp_path, denver_config)
    status_json = status(denver_config)
    assert [j['job_name'] for j in status_json['status']['flat_list']] == [
        'J1-0330',
        'J1-0400',
        'J1-0430',
    ]


def test_repeat_in_family_with_non_repeat_different_lines(tmp_path, denver_config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="0330", every=1800, until="0500")
    J2()
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("F1", family_str, denver_config)
    assert str(exc_info.value) == f"{ex.MSG_FOREST_REPEATING_JOBS_SHOULD_BE_ALONE_IN_FOREST} F1"


def test_repeat_in_family_with_repeat_different_lines(tmp_path, denver_config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="0330", every=1800, until="0500")
    J2(start="0430", every=300, until="0500")
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("F1", family_str, denver_config)
    assert str(exc_info.value) == f"{ex.MSG_FOREST_REPEATING_JOBS_SHOULD_BE_ALONE_IN_FOREST} F1"


def test_repeat_in_family_with_non_repeat_same_lines(tmp_path, denver_config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="0330", every=1800, until="0500") J2()
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("F1", family_str, denver_config)
    assert str(exc_info.value) == f"{ex.MSG_FOREST_REPEATING_JOBS_SHOULD_BE_ALONE_IN_FOREST} F1"


def test_repeat_in_family_with_repeat_same_lines(tmp_path, denver_config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="0330", every=1800, until="0500") J2(start="0430", every=300, until="0500")
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("F1", family_str, denver_config)
    assert str(exc_info.value) == f"{ex.MSG_FOREST_REPEATING_JOBS_SHOULD_BE_ALONE_IN_FOREST} F1"


def test_repeat_in_family_by_itself(tmp_path, denver_config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="0330", every=1800, until="0500")
    -
    J2()
    """
    fam = Family.parse("F1", family_str, denver_config)
    assert fam


def test_mark_success_to_failure(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Ready', 'Ready', 'Ready',
    ]

    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Success', 'Ready', 'Ready',
    ]

    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 1)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Failure', 'Ready', 'Ready',
    ]

def test_mark_success_to_failure_error_code(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    _ = status(two_cal_config_chicago)  # needed to create required dirs
    info_file = create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 1)
    info_dict = tomlkit.loads(pathlib.Path(os.path.join(two_cal_config_chicago.todays_log_dir, info_file)).read_text())
    assert info_dict['error_code'] == 1


def test_mark_success_to_failure_orig_error_code(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    _ = status(two_cal_config_chicago)  # needed to create required dirs
    info_file = create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 1)
    info_dict = tomlkit.loads(pathlib.Path(os.path.join(two_cal_config_chicago.todays_log_dir, info_file)).read_text())
    assert info_dict['original_error_code_20240214_021523'] == 0


def test_mark_success_to_failure_orig_error_code_twice(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    _ = status(two_cal_config_chicago)  # needed to create required dirs
    info_file = create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 1)
    MockDateTime.set_mock(2024, 2, 14, 2, 16, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 0)
    info_dict = tomlkit.loads(pathlib.Path(os.path.join(two_cal_config_chicago.todays_log_dir, info_file)).read_text())
    assert info_dict['original_error_code_20240214_021523'] == 0
    assert info_dict['original_error_code_20240214_021623'] == 1
    assert info_dict['error_code'] == 0


def test_mark_success_to_failure_wrong_name(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    _ = status(two_cal_config_chicago)  # needed to create required dirs
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        mark(two_cal_config_chicago, 'F_UNKNOWN', 'JA', 1)
    assert str(exc_info.value) == f"{ex.MSG_CANT_FIND_SINGLE_JOB_INFO_FILE} F_UNKNOWN:JA"


def test_mark_repeat_job(tmp_path, denver_config):
    prep_repeat_family(tmp_path, denver_config)
    status_json = status(denver_config)
    assert [j['job_name'] for j in status_json['status']['flat_list']] == [
        'J1-0330',
        'J1-0400',
        'J1-0430',
    ]
    info_file = create_job_done_file(denver_config.todays_log_dir, 'F1', 'J1-0330', 'America/Denver', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 3, 31, 23, 'America/Denver')
    mark(denver_config, 'F1', 'J1-0330', 12)
    info_dict = tomlkit.loads(pathlib.Path(os.path.join(denver_config.todays_log_dir, info_file)).read_text())
    assert info_dict['original_error_code_20240214_033123'] == 0
    assert info_dict['error_code'] == 12


def test_hold(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    hold(two_cal_config_chicago, 'F1', 'J6')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'On Hold', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_remove_hold(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    hold(two_cal_config_chicago, 'F1', 'J6')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'On Hold', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_multiple_hold_remove(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    _ = status(two_cal_config_chicago) # to create the dirs
    hold(two_cal_config_chicago, 'F1', 'J6')
    hold(two_cal_config_chicago, 'F1', 'J6')
    hold(two_cal_config_chicago, 'F1', 'J6')
    hold(two_cal_config_chicago, 'F1', 'J6')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'On Hold', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    remove_hold(two_cal_config_chicago, 'F1', 'J6')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_release_deps(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    release_dependencies(two_cal_config_chicago, 'F1', 'J1')  # normally should wait until 3:30
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Ready', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_release_deps_after_run(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    release_dependencies(two_cal_config_chicago, 'F1', 'J1')  # normally should wait until 3:30
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Ready', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    create_job_done_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Success', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_release_deps_after_running(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F3', 'JB', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    create_job_done_file(todays_log_dir, 'F4', 'JC', 'America/Chicago', 'q', 'w', '20240601010203', 0)

    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    release_dependencies(two_cal_config_chicago, 'F1', 'J1')  # normally should wait until 3:30
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Ready', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    create_job_running_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Running', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
