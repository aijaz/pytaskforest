import os

import pytest

from pytf.pytf_worker import start_process, poll_process


def test_start_process(tmp_path):
    script_path = os.path.join(tmp_path, "script.sh")
    with open(script_path, "w") as f:
        f.write("""#!/bin/bash
        sleep 1
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        >&2 echo "this is a line that goes to stderr"
        """)
    os.chmod(script_path, 0o755)
    process = (start_process(script_path))
    error_code = poll_process(process)
    assert error_code == 0


