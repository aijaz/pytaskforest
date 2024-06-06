from app.model.forest import Forest
from app.model.family import Family, Calendar, Days
from app.model.job import Job


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


def test_family_line_one_success_cal():
    family_str = """start="0214", tz = "GMT", calendar="mondays", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse(family_str)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Calendar)
    assert fam.calendar_or_days.calendar_name == 'mondays'


def test_family_line_one_success_days():
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c", days=["Mon", "Wed", "Fri"]
    foo
    bar
    baz
    """
    fam = Family.parse(family_str)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Days)
    assert len(fam.calendar_or_days.days) == 3
    assert 'Mon' in fam.calendar_or_days.days
    assert 'Wed' in fam.calendar_or_days.days
    assert 'Fri' in fam.calendar_or_days.days


def test_family_line_one_success_no_caldays():
    family_str = """start="0214", tz = "GMT", queue="main", email="a@b.c"
    foo
    bar
    baz
    """
    fam = Family.parse(family_str)
    assert fam.start_time_hr == 2
    assert fam.start_time_min == 14
    assert fam.tz == 'GMT'
    assert fam.queue == 'main'
    assert fam.email == 'a@b.c'
    assert isinstance(fam.calendar_or_days, Calendar)
    assert fam.calendar_or_days.calendar_name == 'daily'
