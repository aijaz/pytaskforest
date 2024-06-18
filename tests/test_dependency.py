import datetime

import pytest
import pytz

from pytf.pytf.config import Config
from pytf.pytf.dependency import TimeDependency
from pytf.pytf.mockdatetime import MockDateTime

@pytest.fixture
def denver_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
    """)


def test_time_dependency_unmet(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 6, 1, 1, 59, 59, 'America/Denver')
    assert(d.met() is False)


def test_time_dependency_met(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 6, 1, 2, 0, 0, 'America/Denver')
    assert(d.met() is True)


def test_times(denver_config):
    denver_2 = datetime.datetime(2024, 6, 1, 2, 0, 0, 0, tzinfo=pytz.timezone("America/Denver"))
    chicago_3 = datetime.datetime(2024, 6, 1, 3, 0, 0, 0, tzinfo=pytz.timezone("America/Chicago"))
    la_1 = datetime.datetime(2024, 6, 1, 1, 0, 0, 0, tzinfo=pytz.timezone("America/Los_Angeles"))
    assert(denver_2.timestamp() == chicago_3.timestamp())
    # assert(denver_2.timestamp() == la_1.timestamp())
    # assert(denver_2 == la_1)


def test_time_dependency_met_different_tz(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 6, 1, 1, 0, 0, 'America/Los_Angeles')
    assert(d.met() is True)

