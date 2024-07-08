#!/usr/bin/env python3

import json as j
import os
import logging.config
import logging
import pathlib
import time

import click

from pytf.config import Config
from pytf.exceptions import (PyTaskforestParseException,
                             MSG_CONFIG_MISSING_INSTRUCTIONS_DIR,
                             MSG_CONFIG_MISSING_LOG_DIR,
                             MSG_CONFIG_MISSING_FAMILY_DIR,
                             MSG_CONFIG_MISSING_JOB_DIR,
                             )
from pytf.main import main as pytf_main
from pytf.rerun import rerun as pytf_rerun
from pytf.mark import mark as pytf_mark
from pytf.holdAndRelease import hold as pytf_hold
from pytf.holdAndRelease import remove_hold as pytf_remove_hold
from pytf.holdAndRelease import release_dependencies as pytf_release_dependencies
from pytf.pytf_logging import get_logging_config
from pytf.status import status as pytf_status
from pytf.mockdatetime import MockDateTime
from pytf.pytftoken import PyTfToken


@click.group()
@click.option('--log_dir', help='Log Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--family_dir', help='Family Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--job_dir', help='Job Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--instructions_dir', help='Instructions Directory',
              type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--config_file', help="Config File", type=click.File('r'))
@click.option('--root', help='Main Directory',
              type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.pass_context
def pytf(context,
         log_dir,
         family_dir,
         job_dir,
         instructions_dir,
         config_file,
         root
         ):
    if root is None:
        root = "/pytf_root"

    root_log_dir = os.path.join(root, "logs")
    root_family_dir = os.path.join(root, "families")
    root_job_dir = os.path.join(root, "jobs")
    root_instruction_dir = os.path.join(root, "instructions")
    root_config = os.path.join(root, "config")

    if config_file is None:
        if os.path.exists(root_config):
            config = Config.from_str(pathlib.Path(root_config).read_text())
        else:
            config = Config.from_str("")
    else:
        toml_str = config_file.read()
        config = Config.from_str(toml_str)

    context.obj['config'] = config
    config.log_dir = coalesce(log_dir, config.log_dir, root_log_dir)
    config.family_dir = coalesce(family_dir, config.family_dir, root_family_dir)
    config.job_dir = coalesce(job_dir, config.job_dir, root_job_dir)
    config.instructions_dir = coalesce(instructions_dir, config.instructions_dir, root_instruction_dir)

    if config.log_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_LOG_DIR)
    if config.family_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_FAMILY_DIR)
    if config.job_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_JOB_DIR)
    if config.instructions_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_INSTRUCTIONS_DIR)
    setup_logging(config.log_dir)

    # before doing anything, make sure token file is up-to-date
    # This is important because a rerun may move an info file and cause a token file to point to
    # a non-existent file
    PyTfToken.update_token_usage(config)


def coalesce(d1, d2, root_d):
    if d1 is not None:
        return d1
    if d2 is not None:
        return d2
    return root_d if os.path.exists(root_d) else None


@pytf.command()
@click.pass_context
def main(context):
    logger = logging.getLogger('pytf_logger')
    for i in range(10, 0, -1):
        logger.info(f"{i}")
        time.sleep(1)
    config = context.obj['config']
    pytf_main(config)


@pytf.command()
@click.option("--json", is_flag=True, show_default=True, default=False, help="Output JSON")
@click.option("--collapse", is_flag=True, show_default=True, default=True, help="Collapse Repeating Jobs")
@click.pass_context
def status(context, json, collapse):
    # TODO: Implement collapse functionality: LOW PRIORITY
    def coalesce(r, k):
        return len(r.get(k)) if r.get(k) is not None else 0

    config = context.obj['config']
    statuses = pytf_status(config)

    if json:
        print(j.dumps(statuses))
        return

    flat_list = statuses['status']['flat_list']
    widths = {"fn": 6, "jn": 3, "st": 6, "qn": 5, "tz": 2, "dt": 5, "ec": 3}

    for rec in flat_list:
        widths['fn'] = max(widths['fn'], coalesce(rec, 'family_name'))
        widths['jn'] = max(widths['jn'], coalesce(rec, 'job_name'))
        widths['st'] = max(widths['st'], coalesce(rec, 'status'))
        widths['qn'] = max(widths['qn'], coalesce(rec, 'queue_name'))
        widths['tz'] = max(widths['tz'], coalesce(rec, 'tz'))
        widths['dt'] = max(widths['dt'], coalesce(rec, 'start_time'))

    format_string = f"{{family_name:<{widths['fn']}}} | " + \
                    f"{{job_name:<{widths['jn']}}} | " + \
                    f"{{queue_name:<{widths['qn']}}} | " + \
                    f"{{status:<{widths['st']}}} | " + \
                    f"{{start_time:<{widths['dt']}}} | " + \
                    f"{{tz:<{widths['tz']}}} | " + \
                    f"{{error_code:<{widths['ec']}}} "

    display_time = MockDateTime.now(tz=config.primary_tz)
    print(f"Status as of {display_time.strftime('%Y/%m/%d %H:%M:%S')} ({config.primary_tz})\n")
    print(format_string.format(family_name="Family",
                               job_name="Job",
                               queue_name="Queue",
                               status="Status",
                               start_time="Start",
                               tz="TZ",
                               error_code="Ret"))
    print(format_string.format(family_name="-" * widths['fn'],
                               job_name="-" * widths['jn'],
                               queue_name="-" * widths['qn'],
                               status="-" * widths['st'],
                               start_time="-" * widths['dt'],
                               tz="-" * widths['tz'],
                               error_code="-" * widths['ec'],
                               ))

    for rec in flat_list:
        for possibly_none in ('start_time', 'error_code'):
            rec[possibly_none] = "" if rec[possibly_none] is None else rec[possibly_none]
        print(format_string.format(**rec))


@pytf.command()
@click.argument('family')
@click.argument('job')
@click.pass_context
def rerun(context, family, job):
    config = context.obj['config']
    pytf_rerun(config, family, job)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.argument('--error_code', type=click.IntRange(min=0, max=255))
@click.pass_context
def mark(context, family, job, error_code):
    config = context.obj['config']
    pytf_mark(config, family, job, error_code)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.pass_context
def hold(context, family, job):
    config = context.obj['config']
    pytf_hold(config, family, job)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.pass_context
def remove_hold(context, family, job):
    config = context.obj['config']
    pytf_remove_hold(config, family, job)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.pass_context
def release_dependencies(context, family, job):
    config = context.obj['config']
    pytf_release_dependencies(config, family, job)


def setup_logging(log_dir: str):
    logging_dict = get_logging_config(log_dir)
    logging.config.dictConfig(logging_dict)
    # _ = logging.getLogger('runner')


if __name__ == '__main__':
    pytf(obj={}, auto_envvar_prefix='PYTF')
