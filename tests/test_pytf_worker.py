import os

from pytf.pytf_worker import start_process, poll_process


def test_start_process(tmp_path):
    script_path = os.path.join(tmp_path, "script.sh")
    with open(script_path, "w") as f:
        f.write("""#!/bin/bash
        sleep 1
        >&2 echo "athis is a line that goes to stderr"
        >&2 echo "bthis is a line that goes to stderr"
        >&2 echo "cthis is a line that goes to stderr"
        >&2 echo "dthis is a line that goes to stderr"
        >&2 echo "ethis is a line that goes to stderr"
        >&2 echo "fthis is a line that goes to stderr"
        >&2 echo "gthis is a line that goes to stderr"
        >&2 echo "hthis is a line that goes to stderr"
        >&2 echo "ithis is a line that goes to stderr"
        >&2 echo "jthis is a line that goes to stderr"
        >&2 echo "kthis is a line that goes to stderr"
        >&2 echo "lthis is a line that goes to stderr"
        >&2 echo "mthis is a line that goes to stderr"
        >&2 echo "nthis is a line that goes to stderr"
        >&2 echo "othis is a line that goes to stderr"
        """)
    os.chmod(script_path, 0o755)
    process = (start_process(script_path))
    error_code = poll_process(process)
    assert error_code == 0


