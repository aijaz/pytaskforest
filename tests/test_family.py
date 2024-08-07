import os
import pathlib
import time

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
from pytf.status import status, status_and_families_and_token_doc
from pytf.mark import mark
from pytf.holdAndRelease import (hold, remove_hold, release_dependencies)
from pytf.rerun import rerun
from pytf.pytftoken import PyTfToken
from pytf.runner import prepare_required_dirs
from pytf.main import main, setup_logging_and_tokens, main_with_exception_for_testing


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
def two_token_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
    once_only = true
    run_local = true
    tokens.T3 = 3
    tokens.T2 = 2
    """)


@pytest.fixture
def one_token_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
    once_only = true
    run_local = true
    
    calendars.mondays = [
      "every Monday */*"
    ]
    
    tokens.T1 = 1
    
    """)


@pytest.fixture
def long_running_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
    run_local = true
    
    calendars.mondays = [
      "every Monday */*"
    ]
    
    end_time_hr=3
    end_time_min=0    
    """)


@pytest.fixture
def denver_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
    """)


@pytest.fixture
def empty_cal_config():
    return Config.from_str("""
    calendars.empty = [
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


# def test_split_jobs_missing_paren():
# TODO: Implement this
# line = "J6()  J7() J8() J9() J2("
# with pytest.raises(ex.PyTaskforestParseException) as exc_info:
#     jobs = Forest.split_jobs(line, '')
# # assert str(exc_info.value) == f"{ex.MSG_FAMILY_JOB_TWICE} name::J2"


def test_split_jobs_non_repeat():
    line = "J6()  J7() J8() J9() J2()"
    jobs = Forest.split_jobs(line, '')
    assert [j.job_name for j in jobs] == ['J6', 'J7', 'J8', 'J9', 'J2']


def test_split_jobs_repeat():
    line = "J6(every=900)  J7() J8() J9() J2()"
    jobs = Forest.split_jobs(line, '')
    assert [j.job_name for j in jobs] == ['J6', 'J7', 'J8', 'J9', 'J2']


def test_empty_calendar(empty_cal_config):
    family_str = """start="0214", calendar="empty", tz = "GMT", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse("family", family_str, config=empty_cal_config)
    assert fam
    assert isinstance(fam.calendar_or_days, Calendar)
    cal:Calendar = fam.calendar_or_days
    assert cal.rules == []


def test_days_wrong_type(two_cal_config):
    family_str = """start="0214", days="Mon", tz = "GMT", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value).startswith(ex.MSG_FAMILY_INVALID_TYPE)


def test_log_dir_missing_for_ready_jobs(two_cal_config, tmp_path):
    family_str = """start="0214", email="a@b.c"
    foo
    bar
    baz
    """
    two_cal_config.log_dir = os.path.join(tmp_path, "logs")
    os.makedirs(two_cal_config.log_dir)
    fam = Family.parse("family", family_str, config=two_cal_config)
    jobs = fam.names_of_all_ready_jobs()
    assert jobs is None


def test_unknown_key(two_cal_config):
    family_str = """start="0214", que="main", email="a@b.c"
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value).startswith(ex.MSG_FAMILY_UNRECOGNIZED_PARAM)


def test_tz_wrong_type(two_cal_config):
    family_str = """start="0214", tz = 1, queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value).startswith(ex.MSG_FAMILY_INVALID_TYPE)


def test_no_retry_email_wrong_type(two_cal_config):
    family_str = """start="0214", no_retry_email="False", tz = "GMT", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value).startswith(ex.MSG_FAMILY_INVALID_TYPE)


def test_family_first_line_fail(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="Tuesdays", queue="main", email="a@b.c
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value).startswith(ex.MSG_FAMILY_FIRST_LINE_PARSE_FAIL)


def test_unknown_calendar(two_cal_config):
    family_str = """start="0214", tz = "GMT", calendar="Tuesdays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value) == f"{ex.MSG_FAMILY_UNKNOWN_CALENDAR} Tuesdays"


def test_calendar_and_days_both_specified(two_cal_config):
    family_str = """start="0214", tz = "GMT", days=["Mon", "Wed"], calendar="Tuesdays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        _ = Family.parse("family", family_str, config=two_cal_config)
    assert str(exc_info.value) == ex.MSG_FAMILY_CAL_AND_DAYS


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


def test_external_deps_by_itself(two_cal_config):
    family_str = """start="0000"
     F2::JA()
    """
    fam = Family.parse("name", family_str, two_cal_config)
    assert len(fam.jobs_by_name) == 0


def test_external_deps_by_itself_other_jobs(two_cal_config):
    family_str = """start="0000"
     F2::JA()
     -
     J1()
    """
    fam = Family.parse("name", family_str, two_cal_config)
    assert len(fam.jobs_by_name) == 1
    assert fam.jobs_by_name.get('J1') is not None


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
        f.write(f'num_retries = 0\n')
        f.write(f'retry_sleep = 0\n')
        f.write(f'worker_name = "{w}"\n')
        f.write(f'start_time = "{st}"\n')
        f.write(f'error_code = {ec}\n')
    return file_name


def create_job_running_file(d, fn, jn, tz, q, w, st):
    file_name = f"{fn}.{jn}.{q}.{w}.{st}.info"
    with open(os.path.join(d, file_name), "w") as f:
        f.write(f'family_name = "{fn}"\n')
        f.write(f'job_name = "{jn}"\n')
        f.write(f'tz = "{tz}"\n')
        f.write(f'queue_name = "{q}"\n')
        f.write(f'num_retries = 0\n')
        f.write(f'retry_sleep = 0\n')
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


def test_repeat_inherit_family_end_time(tmp_path, denver_config):
    family_str = """start="0300", queue="main", email="a@b.c"
    J1(start="1930", every=3600)
    """
    fam = Family.parse("F1", family_str, denver_config)
    assert sorted(fam.jobs_by_name.keys()) ==  [
        'J1-1930',
        'J1-2030',
        'J1-2130',
        'J1-2230',
        'J1-2330',
    ]


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
    info_file = create_job_done_file(denver_config.todays_log_dir, 'F1', 'J1-0330', 'America/Denver', 'q', 'w',
                                     '20240601010203', 0)
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

    _ = status(two_cal_config_chicago)  # to create the dirs
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
        'Released', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
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
        'Released', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
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
        'Released', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    create_job_running_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Running', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def test_mark_success_to_failure_then_rerun(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    status_json = status(two_cal_config_chicago)  # needed to create required dirs
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Ready', 'Ready', 'Ready',
    ]
    _ = create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 1)
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Failure', 'Ready', 'Ready',
    ]
    rerun(two_cal_config_chicago, 'F2', 'JA')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Waiting', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Waiting',
        'Released', 'Ready', 'Ready',
    ]


def test_mark_success_to_failure_then_rerun_files(two_cal_config_chicago, tmp_path):
    fam, todays_log_dir = prep_status_family(tmp_path, two_cal_config_chicago)
    _ = status(two_cal_config_chicago)  # needed to create required dirs
    _ = create_job_done_file(todays_log_dir, 'F2', 'JA', 'America/Chicago', 'q', 'w', '20240601010203', 0)
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 23, 'America/Chicago')
    mark(two_cal_config_chicago, 'F2', 'JA', 1)
    rerun(two_cal_config_chicago, 'F2', 'JA')
    files = os.listdir(two_cal_config_chicago.todays_log_dir)
    assert files == ['F2.JA.release', 'F2.JA-Orig-1.q.w.20240601010203.info']


def test_rerun_while_running(two_cal_config_chicago, tmp_path):
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
        'Released', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]
    create_job_running_file(todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203')
    rerun(two_cal_config_chicago, 'F1', 'J1')
    status_json = status(two_cal_config_chicago)
    assert [j['status'] for j in status_json['status']['flat_list']] == [
        'Running', 'Waiting', 'Waiting', 'Waiting', 'Waiting',
        'Ready', 'Ready', 'Ready', 'Ready', 'Ready',
        'Success', 'Success', 'Success',
    ]


def prep_token_family(tmp_path, config, family_str):
    MockDateTime.set_mock(2024, 2, 14, 2, 14, 0, 'America/Chicago')
    config.log_dir = os.path.join(tmp_path, 'log_dir')
    config.family_dir = os.path.join(tmp_path, 'family_dir')
    prepare_required_dirs(config)
    with open(os.path.join(config.todays_family_dir, "F1"), "w") as f:
        f.write(family_str)
    return Family.parse("F1", family_str, config)


def test_token_in_job(one_token_config, tmp_path):
    family_str = """start="0000", queue="main", email="a@b.c"

    J1(tokens=["T1"])
    """
    fam = prep_token_family(tmp_path, one_token_config, family_str)
    ready_job_names = fam.names_of_all_ready_jobs()
    assert ready_job_names == ["J1"]

    j: Job = fam.jobs_by_name['J1']
    t: [str] = j.tokens
    tok_name: str = t[0]
    tok: PyTfToken = one_token_config.tokens_by_name[tok_name]
    assert tok.name == 'T1'
    assert tok.num_instances == 1


def test_two_tokens_in_job(two_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    family_str = """start="0000", queue="main", email="a@b.c"

    J1(tokens=["T2", "T3"])
    """
    fam = prep_token_family(tmp_path, two_token_config, family_str)

    j: Job = fam.jobs_by_name['J1']
    t: [str] = j.tokens
    assert t == ["T2", "T3"]

    tok2: PyTfToken = two_token_config.tokens_by_name['T2']
    assert tok2.name == 'T2'
    assert tok2.num_instances == 2
    tok3: PyTfToken = two_token_config.tokens_by_name['T3']
    assert tok3.name == 'T3'
    assert tok3.num_instances == 3


def test_token_consumption_single_token_available(one_token_config, tmp_path):
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T1"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json = status(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']


def test_token_consumption_single_token_wait_before_running_new_token_doc_created(one_token_config, tmp_path):
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T1"])    J2(tokens=["T1"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert new_token_doc is not None


def test_token_consumption_single_token_wait_before_running_status(one_token_config, tmp_path):
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T1"])    J2(tokens=["T1"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Token Wait']


def test_token_consumption_single_token_wait_after_running(one_token_config, tmp_path):
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T1"])    J2(tokens=["T1"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    PyTfToken.save_token_document(cfg, new_token_doc)
    create_job_running_file(cfg.todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203')
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Running', 'Token Wait']


def test_token_consumption_two_token_available(two_token_config, tmp_path):
    cfg = two_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T2"]) J3(tokens=["T2"]
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json = status(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']


def test_token_consumption_two_token_wait_before_running_new_token_doc_created(two_token_config, tmp_path):
    cfg = two_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T2"])    J2(tokens=["T2"]) J3(tokens=["T2"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert new_token_doc is not None


def test_token_consumption_two_token_wait_before_running_status(two_token_config, tmp_path):
    cfg = two_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T2"])    J2(tokens=["T2"]) J3(tokens=["T2"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Ready', 'Token Wait']


def test_token_consumption_two_token_wait_after_running(two_token_config, tmp_path):
    cfg = two_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
    J1(tokens=["T2"])    J2(tokens=["T2"]) J3(tokens=["T2"])
    """
    fam = prep_token_family(tmp_path, cfg, family_str)

    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    PyTfToken.save_token_document(cfg, new_token_doc)
    create_job_running_file(cfg.todays_log_dir, 'F1', 'J1', 'America/Chicago', 'q', 'w', '20240601010203')
    create_job_running_file(cfg.todays_log_dir, 'F1', 'J2', 'America/Chicago', 'q', 'w', '20240601010203')
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Running', 'Running', 'Token Wait']


def prep_end_to_end(tmp_path, config, families):
    MockDateTime.set_mock(2024, 2, 14, 2, 14, 0, 'America/Denver')
    config.log_dir = os.path.join(tmp_path, 'log_dir')
    config.family_dir = os.path.join(tmp_path, 'family_dir')
    prepare_required_dirs(config)
    for family in families:
        with open(os.path.join(config.todays_family_dir, family['name']), "w") as f:
            f.write(family['str'])
    config.job_dir = os.path.join(tmp_path, 'job_dir')
    dirs.make_dir_if_necessary(config.job_dir)
    for sleep_time, idx in [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
        (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8),
        (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8),
    ]:
        file_path = os.path.join(config.job_dir, f"J{sleep_time}_{idx}")
        with open(file_path, "w") as fp:
            fp.write(f"""#!/bin/bash
            
            echo "Job: J{sleep_time}_{idx}"
            echo "Sleeping for {sleep_time}"
            >&2 echo "This is a line that goes to stderr"
            sleep {sleep_time}
            echo "Done"
            >&2 echo "This is a line that goes to stderr"
            """)
        os.chmod(file_path, 0o755)

        file_path = os.path.join(config.job_dir, f"F{sleep_time}_{idx}")
        with open(file_path, "w") as fp:
            fp.write(f"""#!/bin/bash
            
            echo "Job: F{sleep_time}_{idx}"
            echo "Sleeping for {sleep_time}"
            >&2 echo "This is a line that goes to stderr"
            sleep {sleep_time}
            echo "Done"
            >&2 echo "This is a line that goes to stderr"
            exit 1
            """)
        os.chmod(file_path, 0o755)


def run_main(cfg):
    setup_logging_and_tokens(cfg)
    main(cfg)


def run_main_with_exception_for_testing(cfg):
    setup_logging_and_tokens(cfg)
    main_with_exception_for_testing(cfg)


def test_token_end_to_end_simple(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
J0_1()
J0_2()
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": family_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Waiting']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Ready']
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Success']


def test_token_end_to_end_complex(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c"
    J0_1(tokens=["T1"])
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2(tokens=["T1"])
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str}, {"name": 'F2', "str": f2_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Token Wait']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Token Wait']
    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Ready']
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Success']


def test_rerun_twice_files(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c"
    J0_1()
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success']

    MockDateTime.set_mock(2024, 2, 14, 2, 15, 0, 'America/Denver')
    PyTfToken.update_token_usage(cfg)
    rerun(cfg, 'F1', 'J0_1')
    files = sorted(os.listdir(cfg.todays_log_dir))
    assert files == ['F1.J0_1-Orig-1.default.x.20240214021400.info',
                     'F1.J0_1.log',
                     'F1.J0_1.release']

    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success']

    MockDateTime.set_mock(2024, 2, 14, 2, 16, 0, 'America/Denver')
    PyTfToken.update_token_usage(cfg)
    rerun(cfg, 'F1', 'J0_1')
    files = sorted(os.listdir(cfg.todays_log_dir))
    assert files == ['F1.J0_1-Orig-1.default.x.20240214021400.info',
                     'F1.J0_1-Orig-2.default.x.20240214021500.info',
                     'F1.J0_1.log',
                     'F1.J0_1.release']

    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success']
    files = sorted(os.listdir(cfg.todays_log_dir))
    assert files == ['F1.J0_1-Orig-1.default.x.20240214021400.info',
                     'F1.J0_1-Orig-2.default.x.20240214021500.info',
                     'F1.J0_1.default.x.20240214021600.info',
                     'F1.J0_1.log',
                     'F1.J0_1.release']


def test_hold_when_release_exists(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c"
    J0_1(tokens=["T1"])
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2(tokens=["T1"])
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str}, {"name": 'F2', "str": f2_str}])
    release_dependencies(one_token_config, 'F1', 'J0_1')
    hold(one_token_config, 'F1', 'J0_1')
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['On Hold', 'Ready']
    files = os.listdir(one_token_config.todays_log_dir)
    assert "F1.J0_1.hold" in files
    assert "F1.J0_1.release" not in files


def test_release_when_hold_exists(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c"
    J0_1(tokens=["T1"])
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2(tokens=["T1"])
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str}, {"name": 'F2', "str": f2_str}])
    hold(one_token_config, 'F1', 'J0_1')
    release_dependencies(one_token_config, 'F1', 'J0_1')
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Released', 'Ready']
    files = os.listdir(one_token_config.todays_log_dir)
    assert "F1.J0_1.hold" not in files
    assert "F1.J0_1.release"  in files


def test_end_to_end_fail(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
F0_1()
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": family_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Failure']


def test_end_to_end_cal_exclude(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c", calendar="mondays"
    J0_1()
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2()
    """
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 0, 'America/Denver')

    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str},
                                    {"name": 'F2', "str": f2_str}])
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']
    assert len(families) == 1
    assert families[0].name == 'F2'


def test_end_to_end_day_exclude(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c", days=["Tue", "Thu", "Sat"]
    J0_1()
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2()
    """
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 0, 'America/Denver')

    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str},
                                    {"name": 'F2', "str": f2_str}])
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']
    assert len(families) == 1
    assert families[0].name == 'F2'
    MockDateTime.reset_mock_now()


def test_end_to_end_no_ready_jobs(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="2100", queue="main", email="a@b.c"
    J0_1()
    """
    f2_str = """start="2100", queue="main", email="a@b.c"
    J0_2()
    """
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 0, 'America/Denver')

    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str},
                                    {"name": 'F2', "str": f2_str}])
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Waiting', 'Waiting']
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Waiting', 'Waiting']
    MockDateTime.reset_mock_now()


def test_end_to_end_no_ready_jobs_run_out_of_time(long_running_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = long_running_config
    f1_str = """start="2100", queue="main", email="a@b.c"
    J0_1()
    """
    f2_str = """start="2100", queue="main", email="a@b.c"
    J0_2()
    """
    MockDateTime.set_mock(2024, 2, 14, 2, 15, 0, 'America/Denver')

    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str},
                                    {"name": 'F2', "str": f2_str}])
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Waiting', 'Waiting']
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Waiting', 'Waiting']
    MockDateTime.reset_mock_now()


def test_token_end_to_end_complex_still_running(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c"
    J0_1(tokens=["T1"])
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2(tokens=["T1"])
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str}, {"name": 'F2', "str": f2_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Token Wait']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    # now remove error code to imply it's still running
    info_files = [f for f in os.listdir(one_token_config.todays_log_dir) if f.endswith(".info")]
    assert len(info_files) == 1
    file_name = os.path.join(one_token_config.todays_log_dir, info_files[0])
    file_path = os.path.join(one_token_config.todays_log_dir, file_name)
    file_contents = pathlib.Path(file_path).read_text()
    doc = tomlkit.loads(file_contents)
    del(doc['error_code'])
    new_contents = tomlkit.dumps(doc)
    with open(file_path, "w") as f:
        f.write(new_contents)
    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Running', 'Token Wait']


def test_token_end_to_end_complex_unknown_token(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    f1_str = """start="0000", queue="main", email="a@b.c"
    J0_1(tokens=["T1"])
    """
    f2_str = """start="0000", queue="main", email="a@b.c"
    J0_2(tokens=["T4"])
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": f1_str}, {"name": 'F2', "str": f2_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Token Wait']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    PyTfToken.update_token_usage(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Token Wait']


def test_token_end_to_end_simple_exception(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
J0_1()
J0_2()
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": family_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready', 'Waiting']
    assert cfg.once_only
    assert cfg.run_local
    run_main_with_exception_for_testing(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Ready']
    run_main_with_exception_for_testing(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Success', 'Success']


def test_token_end_to_end_retry(one_token_config, tmp_path):
    # sourcery skip: extract-duplicate-method
    cfg = one_token_config
    family_str = """start="0000", queue="main", email="a@b.c"
F0_1(num_retries=1, retry_sleep=1)
    """
    prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": family_str}])
    print(f"{cfg.log_dir=}")
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']
    assert cfg.once_only
    assert cfg.run_local
    run_main(cfg)
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Failure']
    info_files = [f for f in os.listdir(one_token_config.todays_log_dir) if f.endswith(".info")]
    assert len(info_files) == 1
    file_name = os.path.join(one_token_config.todays_log_dir, info_files[0])
    file_path = os.path.join(one_token_config.todays_log_dir, file_name)
    file_contents = pathlib.Path(file_path).read_text()
    doc = tomlkit.loads(file_contents)
    del doc['error_code']
    del doc['job_pid']
    doc['retry_wait_until'] = int(time.time())
    with open(file_path, "w") as f:
        f.write(tomlkit.dumps(doc))
    status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
    assert [j['status'] for j in status_json['status']['flat_list']] == ['Retry Wait']


# def test_token_end_to_end_retry_wait(one_token_config, tmp_path):
#     # sourcery skip: extract-duplicate-method
#     cfg = one_token_config
#     family_str = """start="0000", queue="main", email="a@b.c"
# F0_1(num_retries=1, retry_sleep=1)
#     """
#     prep_end_to_end(tmp_path, cfg, [{"name": 'F1', "str": family_str}])
#     print(f"{cfg.log_dir=}")
#     status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
#     assert [j['status'] for j in status_json['status']['flat_list']] == ['Ready']
#     assert cfg.once_only
#     assert cfg.run_local
#     run_main(cfg)
#     status_json, families, new_token_doc = status_and_families_and_token_doc(cfg)
#     assert [j['status'] for j in status_json['status']['flat_list']] == ['Failure']
#
