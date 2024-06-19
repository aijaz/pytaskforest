import pytest

from pytf.exceptions import (
    PyTaskforestParseException,
    MSG_FAMILY_JOB_TWICE,
)
from pytf.forest import Forest
from pytf.family import Family
from pytf.days import Days
from pytf.calendar import Calendar
from pytf.job import Job
from pytf.config import Config


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


def test_family_split_single():
    line = " J()"
    jobs = Forest.split_jobs(line)
    assert (len(jobs) == 1)


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
    assert (len(jobs) == 2)


def test_family_split_double_data():
    line = 'J(tz = "GMT", chained=TRUE) E(tz = "America/Denver", start="0200") # foo'
    jobs = Forest.split_jobs(line)
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
    assert fam.forests[0].jobs[0][1].job_name == 'J2'
    assert fam.forests[0].jobs[1][0].job_name == 'J3'
    assert fam.forests[0].jobs[2][0].job_name == 'J4'
    assert fam.forests[0].jobs[2][1].job_name == 'J5'


def test_full_family_line_one_forest_plus_one_empty(two_cal_config):
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"

    J1() J2() # bar
    # foo
      J3() # foo
    J4() J5()
    ---
    # foo
    """
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
    with pytest.raises(PyTaskforestParseException) as excinfo:
        fam = Family.parse("name", family_str, two_cal_config)
    assert str(excinfo.value) == f"{MSG_FAMILY_JOB_TWICE} name::J2"
