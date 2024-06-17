import os
import pytz

from pytf.pytf.mockdatetime import MockDateTime
from pytf.pytf.dirs import dated_dir
from pytf.pytf.main import make_family_dir_if_necessary

def test_make_family_dir_if_necessary(tmp_path):
    MockDateTime.set_mock(2024, 6, 3, 1, 2, 3, pytz.timezone('America/Denver'))
    dest = dated_dir(os.path.join(tmp_path, "{YYYY}-{MM}-{DD}"), MockDateTime.now())
    assert(dest == os.path.join(tmp_path, "2024-06-03"))

