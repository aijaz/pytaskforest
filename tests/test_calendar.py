import datetime

import pytest

from pytf.pytf_calendar import Calendar
import pytf.exceptions as ex

cal_params = [
    ('every_day', (2024, 6, 6, True, ['+ */*/*'])),
    ('every_day_no_plus-m', (2024, 6, 6, True, ['*/*/*'])),
    ('specific_date', (2024, 6, 6, True, ['+ 2024/06/06'])),
    ('specific_date_nopm', (2024, 6, 6, True, ['2024/06/06'])),
    ('month_wc', (2024, 6, 6, True, ['+ 2024/*/06'])),
    ('month_wc_nopm', (2024, 6, 6, True, ['2024/*/06'])),
    ('day_wc', (2024, 6, 6, True, ['+ 2024/06/*'])),
    ('day_wc_nopm', (2024, 6, 6, True, ['2024/06/*'])),
    ('md_wc', (2024, 6, 6, True, ['+ 2024/*/*'])),
    ('md_wc_nopm', (2024, 6, 6, True, ['2024/*/*'])),
    ('yd_wc', (2024, 6, 6, True, ['+ */06/*'])),
    ('yd_wc_nopm', (2024, 6, 6, True, ['*/06/*'])),
    ('ym_wc', (2024, 6, 6, True, ['+ */*/06'])),
    ('ym_wc_nopm', (2024, 6, 6, True, ['*/*/06'])),

    ('every_day_but_this', (2024, 6, 6, False, ['+ */*/*', '- 2024/06/6'])),

    ('first_fri_202406', (2024, 6, 7, True, ['+ first fri 2024/06'])),
    ('first_fri_202406', (2024, 6, 7, True, ['first fri 2024/06'])),
    ('first_fri_202406', (2024, 6, 6, False, ['first fri 2024/06'])),

    ('every_day_but_f_fri', (2024, 6, 7, False, ['+ */*/*', '- first fri 2024/06'])),
    ('every_day_but_f_fri', (2024, 6, 7, False, ['+ */*/*', '- first fri 2024/*'])),
    ('every_day_but_f_fri_7', (2024, 6, 7, True, ['+ */*/*', '- first fri 2024/*', '*/*/7'])),

    ('MWF', (2024, 6, 2, False, ['every mon */*', 'every wed */*', 'every Fri */*', ])),
    ('MWF', (2024, 6, 4, False, ['every mon */*', 'every wed */*', 'every Fri */*', ])),
    ('MWF', (2024, 6, 6, False, ['every mon */*', 'every wed */*', 'every Fri */*', ])),
    ('MWF', (2024, 6, 8, False, ['every mon */*', 'every wed */*', 'every Fri */*', ])),
    ('MWF', (2024, 6, 10, True, ['every mon */*', 'every wed */*', 'every Fri */*', ])),
    ('MWF', (2024, 6, 14, True, ['every mon */*', 'every wed */*', 'every Fri */*', ])),
    ('MWF', (2024, 6, 12, True, ['every mon */*', 'every wed */*', 'every Fri */*', ])),

    #       June 2024
    #  Su Mo Tu We Th Fr Sa
    #                     1
    #   2  3  4  5  6  7  8
    #   9 10 11 12 13 14 15
    #  16 17 18 19 20 21 22
    #  23 24 25 26 27 28 29
    #  30

    ('last Sun', (2024, 6, 30, True, ['last Sun */* ', ])),
    ('fifth Sun', (2024, 6, 30, True, ['fifth Sun */* ', ])),
    ('fifth Sun', (2024, 6, 30, True, ['FIFTH SUN */* ', ])),
    ('fourth Sun', (2024, 6, 30, False, ['fourth SUN */* ', ])),
    ('2nd last Sun', (2024, 6, 30, False, ['secOnD last Sun */* ', ])),

    ('last Sun', (2024, 6, 30, True, ['first last Sun */* ', ])),
    ('2nd last Sun', (2024, 6, 23, True, ['secOnD last Sun */* ', ])),
    ('3rd last Sun', (2024, 6, 16, True, ['third last Sun */* ', ])),
    ('4th last Sun', (2024, 6, 9, True, ['fourth last Sun */* ', ])),
    ('5th last Sun', (2024, 6, 2, True, ['fifth last Sun */* ', ])),

    ('last Sun', (2024, 6, 30, True, ['first last Sun */* ', ])),
    ('2nd last Sun', (2024, 6, 23, True, ['secOnD last Sun */* ', ])),
    ('3rd last Sun', (2024, 6, 16, True, ['third last Sun */* ', ])),
    ('4th last Sun', (2024, 6, 9, True, ['fourth last Sun */* ', ])),
    ('5th last Sun', (2024, 6, 2, True, ['fifth last Sun */* ', ])),

    ('last Sun', (2024, 6, 23, False, ['first last Sun */* ', ])),
    ('2nd last Sun', (2024, 6, 30, False, ['secOnD last Sun */* ', ])),
    ('3rd last Sun', (2024, 6, 9, False, ['third last Sun */* ', ])),
    ('4th last Sun', (2024, 6, 2, False, ['fourth last Sun */* ', ])),
    ('5th last Sun', (2024, 6, 16, False, ['fifth last Sun */* ', ])),

    ('5th Thu', (2024, 7, 25, False, ['fifth Thu */* ', ])),
    ('not today', (2024, 7, 25, False, ['2024/7/26 ', ])),
    ('not today', (2024, 7, 25, False, ['2024/7/26 ', ])),
    ('today', (2024, 7, 25, True, ['2024/7/26 ', 'every Thu */*'])),

]


@pytest.mark.parametrize(["yyyy", "mm", "dd", "match", "rules"],
                         [i[1] for i in cal_params],
                         ids=[v[0] for v in cal_params]
                         )
def test_cal_match(yyyy, mm, dd, match, rules):
    c = Calendar(calendar_name='cal', rules=rules)
    assert c.is_date_included(yyyy, mm, dd) == match


def test_calendar_default():
    c = Calendar("cal")
    assert c.rules == []


fail_params = [
    ('invalid_rule', ('', f"{ex.MSG_CALENDAR_INVALID_RULE} ")),
    ('dangling offset', ('every', f"{ex.MSG_CALENDAR_DANGLING_OFFSET} every")),
    ('dangling offset last', ('last', f"{ex.MSG_CALENDAR_DANGLING_OFFSET} last")),
    ('dangling offset second last', ('second last', f"{ex.MSG_CALENDAR_DANGLING_OFFSET} second")),
    ('invalid_date_standalone--', ('3/4', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/4")),
    ('invalid_date_standalone-p', ('+ 3/4', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/4")),
    ('invalid_date_standalone-m', ('- 3/4', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/4")),
    ('too_many_components--', ('3/4/2014/1', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/4/2014/1")),
    ('too_many_components-p', ('+ 3/4/2014/1', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/4/2014/1")),
    ('too_many_components-m', ('- 3/4/2014/1', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/4/2014/1")),
    ('offset_and_date--', ('every 12/4/2014', f"{ex.MSG_CALENDAR_UNKNOWN_WEEKDAY} 12/")),
    ('offset_and_date-p', ('+ every 12/4/2014', f"{ex.MSG_CALENDAR_UNKNOWN_WEEKDAY} 12/")),
    ('offset_and_date-m', ('- every 12/4/2014', f"{ex.MSG_CALENDAR_UNKNOWN_WEEKDAY} 12/")),
    ('offset_and_date_second_last--', ('second last 12/4/2014', f"{ex.MSG_CALENDAR_UNKNOWN_WEEKDAY} 12/")),
    ('offset_and_date_second_last-p', ('+ second last 12/4/2014', f"{ex.MSG_CALENDAR_UNKNOWN_WEEKDAY} 12/")),
    ('offset_and_date_second_last-m', ('- second last 12/4/2014', f"{ex.MSG_CALENDAR_UNKNOWN_WEEKDAY} 12/")),
    ('non_int_yyyy', ('3/5/TwoThousandZeroZero', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/5/TwoThousandZeroZero")),
    ('non_int_yyyy_p', ('+ 3/5/TwoThousandZeroZero', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/5/TwoThousandZeroZero")),
    ('non_int_yyyy_m', ('- 3/5/TwoThousandZeroZero', f"{ex.MSG_CALENDAR_INVALID_DATE} 3/5/TwoThousandZeroZero")),
    ('offset_and_date_first_friday--', ('first fri 12/4/2014', f"{ex.MSG_CALENDAR_OFFSET_AND_DATE} 12/4/2014")),
    ('offset_and_date_first_friday-p', ('+ first fri 12/4/2014', f"{ex.MSG_CALENDAR_OFFSET_AND_DATE} 12/4/2014")),
    ('offset_and_date_first_friday-m', ('- first fri 12/4/2014', f"{ex.MSG_CALENDAR_OFFSET_AND_DATE} 12/4/2014")),
]


@pytest.mark.parametrize(["rule", "error"],
                         [i[1] for i in fail_params],
                         ids=[i[0] for i in fail_params]
                         )
def test_cal_fail(rule, error):
    c = Calendar(calendar_name='cal', rules=[rule])
    naive_date = datetime.date(2024, 1, 1)
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        m = c.does_rule_match(naive_date, naive_date.weekday(), c.rules[0])
    assert str(exc_info.value) == error



#
# def test_calendar_non_int_yyyy():
#     c = Calendar("cal", ["3/5/TwoThousandZeroZero"])
#     naive_date = datetime.date(2024, 1, 1)
#     with pytest.raises(ex.PyTaskforestParseException) as exc_info:
#         m = c.does_rule_match(naive_date, naive_date.weekday(), c.rules[0])
#     assert str(exc_info.value) == f"{ex.MSG_CALENDAR_DANGLING_OFFSET} 3/4"
