import subprocess
import logging
import time


def setup_logger(log_file, logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def run_shell_script(script_path, run_logger):

    process = subprocess.Popen(
        script_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    while True:
        if line := process.stdout.readline().decode('utf-8').strip():
            run_logger.info(line)
        if line := process.stderr.readline().decode('utf-8').strip():
            run_logger.error(line)
        if (err_code := process.poll()) is not None:
            # clean up any remaining lines from the buffers
            while line := process.stdout.readline().decode('utf-8').strip():
                run_logger.info(line)
            while line := process.stderr.readline().decode('utf-8').strip():
                run_logger.error(line)
            if err_code:
                run_logger.error(f"Process failed with error code {err_code}")
            else:
                run_logger.info(f"Process completed with return code {err_code}")
            break
        time.sleep(0.1)

    process.stdout.close()
    process.stderr.close()
    return err_code


if __name__ == '__main__':
    script_path = '/path_to_your_script.sh'
    stdout_log = 'stdout.log'
    the_logger = setup_logger(stdout_log, 'run')
    run_shell_script(script_path, the_logger)
