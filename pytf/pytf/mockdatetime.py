import time
from datetime import datetime
from typing import Optional


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
                 tz
                 ) -> None:
        cls._mock_now = datetime(YYYY, MM, DD, h, m, s, 0, tz)

    @classmethod
    def reset_mock_now(cls) -> None:
        cls._mock_now = None

    @classmethod
    def now(cls, tz=None) -> datetime:
        return cls._mock_now if cls._mock_now is not None else datetime.now(tz=tz)


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