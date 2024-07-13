import time
from datetime import datetime, timezone, timedelta
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
        cls.set_mock_now(pytz.timezone(tz).localize(datetime(YYYY, MM, DD, h, m, s, 0)))

    @classmethod
    def reset_mock_now(cls) -> None:
        cls._mock_now = None

    @classmethod
    def now(cls, tz: str = "UTC") -> datetime:
        return cls._mock_now.astimezone(pytz.timezone(tz)) \
            if cls._mock_now is not None \
            else datetime.now(timezone.utc).astimezone(pytz.timezone(tz))

    @classmethod
    def sleep(cls, s):
        func = time.sleep if cls._mock_now is None else cls._mock_sleep
        func(s)

    @classmethod
    def _mock_sleep(cls, s):
        cls._mock_now = cls._mock_now + timedelta(seconds=s)


    @classmethod
    def dow(cls, tz: str = "UTC") -> str:
        index = cls.now(tz).weekday()
        return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][index]

