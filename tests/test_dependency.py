import datetime

import pytest
import pytz

from pytf.config import Config
from pytf.dependency import Dependency, TimeDependency
from pytf.mockdatetime import MockDateTime


@pytest.fixture
def denver_config():
    return Config.from_str("""
    primary_tz = "America/Denver"
    """)


def test_time_dependency_unmet(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 5, 1, 1, 59, 59, 'America/Denver')
    assert (d.met() is False)


def test_time_dependency_met(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 6, 1, 2, 0, 0, 'America/Denver')
    assert (d.met() is True)


def test_times_denver_chicago(denver_config):
    denver_2 = pytz.timezone("America/Denver").localize(datetime.datetime(2024, 6, 1, 2, 0, 0, 0))
    chicago_3 = pytz.timezone("America/Chicago").localize(datetime.datetime(2024, 6, 1, 3, 0, 0, 0))
    assert (denver_2.timestamp() == chicago_3.timestamp())


def test_times_denver_la(denver_config):
    denver_2 = pytz.timezone("America/Denver").localize(datetime.datetime(2024, 6, 1, 2, 0, 0, 0))
    la_1 = pytz.timezone("America/Los_Angeles").localize(datetime.datetime(2024, 6, 1, 1, 0, 0, 0))
    assert (denver_2.timestamp() == la_1.timestamp())
    assert (denver_2 == la_1)


def test_time_dependency_met_different_tz(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 6, 1, 1, 0, 0, 'America/Los_Angeles')
    assert (d.met() is True)


def test_time_dependency_met_different_tz_2(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 6, 1, 4, 0, 0, 'America/New_York')
    assert (d.met() is True)


def test_time_dependency_unmet_2(denver_config):
    d = TimeDependency(config=denver_config, hh=2, mm=0, tz="America/Denver")
    MockDateTime.set_mock(2024, 5, 1, 2, 59, 59, 'America/New_York')
    assert (d.met() is False)


def test_met(denver_config):
    a = Dependency(denver_config)
    assert a.met(user_info=None) is False
