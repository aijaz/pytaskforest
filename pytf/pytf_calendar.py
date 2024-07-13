import datetime
import calendar

from attrs import define, field

import pytf.exceptions as ex

@define
class Calendar:
    calendar_name: str
    rules: [str] = field()

    @rules.default
    def _rules(self):
        return []

    def is_date_included(self, yyyy: int, mm: int, dd: int) -> bool:
        naive_dt = datetime.date(yyyy, mm, dd)
        naive_dow = naive_dt.weekday()

        result = False

        for rule in self.rules:
            match = self.does_rule_match(naive_dt, naive_dow, rule)
            if match is not None:
                result = match

        return result

    def does_rule_match(self, naive_date, naive_dow, rule) -> bool | None:
        plus_or_minus = '+'
        components = rule.split()
        if len(components) == 0:
            raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_INVALID_RULE} rule")
        elif len(components) > 1 and components[0] in '-+':
            plus_or_minus = components.pop(0)

        nth = None
        dow = None
        offsets = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "last": -1,
            "every": 0,
        }
        if components[0].lower() in offsets:
            if len(components) < 2:
                raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_DANGLING_OFFSET} {components[0]}")

            nth = offsets[components[0].lower()]
            if components[1].lower() == 'last':
                nth = nth * -1 if nth > 0 else -1
                del (components[1])  # get rid of 'last'

            if len(components) < 2:
                raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_DANGLING_OFFSET} {components[0]}")

            dows = {
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            dow = dows[components[1][:3].lower()]

            # get rid of first 2 components
            components.pop(0)
            components.pop(0)

        if components[0]:
            yyyymmdd = components[0]
            date_components = yyyymmdd.split('/')
            if len(date_components) > 3:
                raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_INVALID_DATE} {yyyymmdd}")

            if nth is not None and len(date_components) == 3:
                raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_OFFSET_AND_DATE} {yyyymmdd}")

            yyyy, mm, dd = '*', '*', '*'
            if len(date_components) >= 1:
                yyyy = date_components[0]
            if len(date_components) >= 2:
                mm = date_components[1]
            if len(date_components) == 3:
                dd = date_components[2]

            try:
                if yyyy != '*':
                    yyyy = int(yyyy)
                if mm != '*':
                    mm = int(mm)
                if dd != '*':
                    dd = int(dd)
            except ValueError as e:
                raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_INVALID_DATE} {yyyymmdd}") from e

            if (yyyy != '*' and yyyy < 1970) or (mm != '*' and (mm < 1 or mm > 12)) or (dd != '*' and (dd < 1 or dd > 31)):
                raise ex.PyTaskforestParseException(f"{ex.MSG_CALENDAR_INVALID_DATE} {yyyymmdd}")

            # now try to eliminate based on yyyy mm and dd

            keep_going = False

            if (
                yyyy in ['*', naive_date.year]
                and mm in ['*', naive_date.month]
                and dd in ['*', naive_date.day]
            ):
                keep_going = True
                yyyy = naive_date.year
                mm = naive_date.month
                dd = naive_date.day

            if not keep_going:
                return None

            # now we know that the date part matches.
            # now check for the day of week part, if present

            if nth is None or dow is None:
                return plus_or_minus == '+'

            if dow == naive_dow:
                # check nth
                # check easy ones first

                if nth == 0:
                    return plus_or_minus == '+'

                # find days of week
                dates = self.find_days_of_week(yyyy, mm, dow)

                if nth > 0:
                    nth -= 1  # so we can use it as an array subscript

                if nth == 4 and len(dates) < 5:
                    return False  # fifth dow does not exist

                return plus_or_minus == '+' if dates[nth] == naive_date.day else None
            else:
                return None

    def find_days_of_week(self, yyyy, mm, dow):
        """
        #returns an array of 4 or 5 mdays, each of which correspond to the nth dow of y/m

        :param yyyy:
        :param mm:
        :param dow:
        :return:
        """
        # find the day of week of the first
        naive_first_of_month = datetime.datetime(yyyy, mm, 1)
        naive_dow_of_first = naive_first_of_month.weekday()

        # mon = 0
        # thu = 3                                                   1                   2                   3
        # naive_dow_of_first   dow   first_dd     1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        # 0                    3     4            M T W R F S S M T W R F S S M T W R F S S M T W R F S S M T W
        # 1                    3     3            T W R F S S M T W R F S S M T W R F S S M T W R F S S M T W R
        # 2                    3     2            W R F S S M T W R F S S M T W R F S S M T W R F S S M T W R F
        # 3                    3     1            R F S S M T W R F S S M T W R F S S M T W R F S S M T W R F S
        # 4                    3     7            F S S M T W R F S S M T W R F S S M T W R F S S M T W R F S S
        # 5                    3     6            S S M T W R F S S M T W R F S S M T W R F S S M T W R F S S M
        # 6                    3     5            S M T W R F S S M T W R F S S M T W R F S S M T W R F S S M T

        result = [
            (
                1 + dow - naive_dow_of_first
                if naive_dow_of_first <= dow
                else 8 - (naive_dow_of_first - dow)
            )
        ]
        days_in_month = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if calendar.isleap(yyyy):
            days_in_month[2] += 1

        days_in_this_month = days_in_month[mm]

        next_dd = result[0] + 7
        while next_dd <= days_in_this_month:
            result.append(next_dd)
            next_dd += 7

        return result
