import pytest

from app.model.calendar import Calendar

cal_params = [
    ('every_day',              (2024, 6, 6, True, ['+ */*/*'])),
    ('every_day_no_plus_minus',(2024, 6, 6, True, ['*/*/*'])),
    ('specific_date',          (2024, 6, 6, True, ['+ 2024/06/06'])),
    ('specific_date_nopm',     (2024, 6, 6, True, ['2024/06/06'])),
    ('month_wc',               (2024, 6, 6, True, ['+ 2024/*/06'])),
    ('month_wc_nopm',          (2024, 6, 6, True, ['2024/*/06'])),
    ('day_wc',                 (2024, 6, 6, True, ['+ 2024/06/*'])),
    ('day_wc_nopm',            (2024, 6, 6, True, ['2024/06/*'])),
    ('md_wc',                  (2024, 6, 6, True, ['+ 2024/*/*'])),
    ('md_wc_nopm',             (2024, 6, 6, True, ['2024/*/*'])),
    ('yd_wc',                  (2024, 6, 6, True, ['+ */06/*'])),
    ('yd_wc_nopm',             (2024, 6, 6, True, ['*/06/*'])),
    ('ym_wc',                  (2024, 6, 6, True, ['+ */*/06'])),
    ('ym_wc_nopm',             (2024, 6, 6, True, ['*/*/06'])),

    ('every_day_but_this',     (2024, 6, 6, False, ['+ */*/*', '- 2024/06/6'])),

    ('first_fri_202406',       (2024, 6, 7, True, ['+ first fri 2024/06'])),
    ('first_fri_202406',       (2024, 6, 7, True, ['first fri 2024/06'])),
    ('first_fri_202406',       (2024, 6, 6, False, ['first fri 2024/06'])),

    ('every_day_but_f_fri',    (2024, 6, 7, False, ['+ */*/*', '- first fri 2024/06'])),
    ('every_day_but_f_fri',    (2024, 6, 7, False, ['+ */*/*', '- first fri 2024/*'])),
    ('every_day_but_f_fri_7',  (2024, 6, 7, True, ['+ */*/*', '- first fri 2024/*', '*/*/7'])),

    ]


@pytest.mark.parametrize(["yyyy", "mm", "dd", "match", "rules"],
                         [i[1] for i in cal_params],
                         ids=[v[0] for v in cal_params]
                         )
def test_cal_match(yyyy, mm, dd, match, rules):
    c = Calendar(calendar_name='cal', rules=rules)
    assert c.is_date_included(yyyy, mm, dd) == match

