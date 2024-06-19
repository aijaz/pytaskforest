import os

import pytest

from pytf.pytf.job_result import JobResult
from pytf.pytf.job_status import JobStatus
from pytf.pytf.logs import get_logged_jobs

def test_get_logged_jobs(tmp_path):
    with open(os.path.join(tmp_path, "f1.j1.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "f1"\n')
        f.write('job_name = "j1"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')

    with open(os.path.join(tmp_path, "f1.j2.q1.w1.20240601010204.info"), "w") as f:
        f.write('family_name = "f1"\n')
        f.write('job_name = "j2"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:04"\n')
        f.write('error_code = 0\n')

    with open(os.path.join(tmp_path, "f1.j3.q1.w1.20240601010205.info"), "w") as f:
        f.write('family_name = "f1"\n')
        f.write('job_name = "j3"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:05"\n')
        f.write('error_code = 127\n')

    job_results:[JobResult] = get_logged_jobs(str(tmp_path))

    assert(job_results[0].family_name == 'f1')
    assert(job_results[0].job_name == 'j1')
    assert(job_results[0].tz == 'America/Chicago')
    assert(job_results[0].queue_name == 'q1')
    assert(job_results[0].worker_name == 'w1')
    assert(job_results[0].start_time == '2024/06/01 02:02:03')
    assert(job_results[0].error_code is None)
    assert(job_results[0].status == JobStatus.RUNNING)

    assert(job_results[1].family_name == 'f1')
    assert(job_results[1].job_name == 'j2')
    assert(job_results[1].tz == 'America/Chicago')
    assert(job_results[1].queue_name == 'q1')
    assert(job_results[1].worker_name == 'w1')
    assert(job_results[1].start_time == '2024/06/01 02:02:04')
    assert(job_results[1].error_code == 0)
    assert(job_results[1].status == JobStatus.SUCCESS)

    assert(job_results[2].family_name == 'f1')
    assert(job_results[2].job_name == 'j3')
    assert(job_results[2].tz == 'America/Chicago')
    assert(job_results[2].queue_name == 'q1')
    assert(job_results[2].worker_name == 'w1')
    assert(job_results[2].start_time == '2024/06/01 02:02:05')
    assert(job_results[2].error_code == 127)
    assert(job_results[2].status == JobStatus.FAILURE)

