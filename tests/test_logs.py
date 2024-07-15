import os

from pytf.job_status import JobStatus
from pytf.logs import get_logged_job_results


# Don't need to test this too much because we're mostly testing tomlkit
def test_get_logged_job_results_family_name(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].family_name == 'f1')


def test_get_logged_job_results_job_name(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].job_name == 'j1')


def test_get_logged_job_results_tz(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].tz == 'America/Chicago')


def test_get_logged_job_results_queue_name(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].queue_name == 'q1')


def test_get_logged_job_results_worker_name(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].worker_name == 'w1')


def test_get_logged_job_results_start_time(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].start_time == '2024/06/01 02:02:03')


def test_get_logged_job_results_error_code_none(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].error_code is None)


def test_get_logged_job_results_job_status_running(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[0].status == JobStatus.RUNNING)


def test_get_logged_job_results_error_code_zero(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[1].error_code == 0)


def test_get_logged_job_results_job_status_success(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[1].status == JobStatus.SUCCESS)


def test_get_logged_job_results_error_code_127(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[2].error_code == 127)


def test_get_logged_job_results_job_status_failure(tmp_path):
    job_dict, job_list = prep_log_files(tmp_path)
    assert (job_list[2].status == JobStatus.FAILURE)


def test_get_logged_job_results_sort_order(tmp_path):
    d, l = prep_log_files(tmp_path)

    assert (d['f1']['j1'] == l[0])
    assert (d['f1']['j2'] == l[1])
    assert (d['f1']['j3'] == l[2])


def prep_log_files(tmp_path):
    with open(os.path.join(tmp_path, "f1.j1.q1.w1.20240601010203.info"), "w") as f:
        f.write('family_name = "f1"\n')
        f.write('job_name = "j1"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write(f'num_retries = 0\n')
        f.write(f'retry_sleep = 0\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:03"\n')
    with open(os.path.join(tmp_path, "f1.j2.q1.w1.20240601010204.info"), "w") as f:
        f.write('family_name = "f1"\n')
        f.write('job_name = "j2"\n')
        f.write('tz = "America/Chicago"\n')
        f.write('queue_name = "q1"\n')
        f.write(f'num_retries = 0\n')
        f.write(f'retry_sleep = 0\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:04"\n')
        f.write('error_code = 0\n')
    with open(os.path.join(tmp_path, "f1.j3.q1.w1.20240601010205.info"), "w") as f:
        f.write('family_name = "f1"\n')
        f.write('job_name = "j3"\n')
        f.write('tz = "America/Chicago"\n')
        f.write(f'num_retries = 0\n')
        f.write(f'retry_sleep = 0\n')
        f.write('queue_name = "q1"\n')
        f.write('worker_name = "w1"\n')
        f.write('start_time = "2024/06/01 02:02:05"\n')
        f.write('error_code = 127\n')
    job_list, job_dict = get_logged_job_results(str(tmp_path))
    return job_dict, job_list