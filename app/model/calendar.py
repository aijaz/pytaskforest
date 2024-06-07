from datetime import (datetime)

from attrs import define, field
import pytz


@define
class Calendar:
    calendar_name: str
    rules: [str] = field(default=[])

    def is_date_included(self, ):
        pass
