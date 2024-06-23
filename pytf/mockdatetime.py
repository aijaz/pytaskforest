import time
from datetime import datetime, timezone
from typing import Optional

import pytz


class MockDateTime:
    _mock_now: Optional[datetime] = None

    @classmethod
    def set_mock_now(cls, mock_now: datetime) -> None:
        cls._mock_now = mock_now

    @classmethod
    def set_mock(cls,
                 YYYY: int,
                 MM: int,
                 DD: int,
                 h: int,
                 m: int,
                 s: int,
                 tz: str
                 ) -> None:
        cls._mock_now = pytz.timezone(tz).localize(datetime(YYYY, MM, DD, h, m, s, 0))

    @classmethod
    def reset_mock_now(cls) -> None:
        cls._mock_now = None

    @classmethod
    def now(cls, tz: str="UTC") -> datetime:
        return cls._mock_now.astimezone(pytz.timezone(tz)) if cls._mock_now is not None else datetime.now(timezone.utc).astimezone(pytz.timezone(tz))


class MockSleep:
    _sleep_should_be_mocked: bool = False

    @classmethod
    def mock_sleep(cls):
        cls._sleep_should_be_mocked = True

    @classmethod
    def dont_mock_sleep(cls):
        cls._sleep_should_be_mocked = False

    @classmethod
    def sleep(cls, seconds: int):
        if cls._sleep_should_be_mocked:
            return
        time.sleep(seconds)