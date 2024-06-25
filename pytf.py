#!/usr/bin/env python3

import json
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
from pytf.hold import hold as pytf_hold
from pytf.pytf_logging import get_logging_config
from pytf.status import status as pytf_status
from pytf.release_hold import release_hold as pytf_release_hold

logger = logging.getLogger('pytf_logger')

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


def coalesce(d1, d2, root_d):
    if d1 is not None:
        return d1
    if d2 is not None:
        return d2
    return root_d if os.path.exists(root_d) else None


@pytf.command()
@click.pass_context
def main(context):
    for i in range(10, 0, -1):
        logger.info(f"{i}")
        time.sleep(1)
    config = context.obj['config']
    pytf_main(config)


@pytf.command()
@click.pass_context
def status(context):
    config = context.obj['config']
    status = pytf_status(config)
    print(json.dumps(status))


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
def release_hold(context, family, job):
    config = context.obj['config']
    pytf_release_hold(config, family, job)


def setup_logging(log_dir: str):
    logging.config.dictConfig(get_logging_config(log_dir))
    _ = logging.getLogger('runner')


if __name__ == '__main__':
    pytf(obj={}, auto_envvar_prefix='PYTF')
