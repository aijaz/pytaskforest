#!/usr/bin/env python3

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
from pytf.release_hold import release_hold as pytf_release_hold


@click.group()
@click.option('--log_dir', help='Log Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--family_dir', help='Family Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--job_dir', help='Job Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--instructions_dir', help='Instructions Directory',
              type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--config_file', help="Config File", type=click.File('r'))
@click.pass_context
def pytf(context,
         log_dir,
         family_dir,
         job_dir,
         instructions_dir,
         config_file
         ):
    if config_file is not None:
        toml_str = config_file.read()
        config = Config.from_str(toml_str)
    else:
        config = Config(toml_str="")

    context.obj['config'] = config
    config.log_dir = log_dir if log_dir is not None else config.log_dir
    config.family_dir = family_dir if family_dir is not None else config.family_dir
    config.job_dir = job_dir if job_dir is not None else config.job_dir
    config.instructions_dir = instructions_dir if instructions_dir is not None else config.instructions_dir

    if config.log_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_LOG_DIR)
    if config.family_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_FAMILY_DIR)
    if config.job_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_JOB_DIR)
    if config.instructions_dir is None:
        raise PyTaskforestParseException(MSG_CONFIG_MISSING_INSTRUCTIONS_DIR)


@pytf.command()
@click.pass_context
def main(context):
    config = context.obj['config']
    pytf_main(config)


@pytf.command()
@click.pass_context
def status(context):
    config = context.obj['config']
    pytf_main(config)


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


if __name__ == '__main__':
    pytf(obj={}, auto_envvar_prefix='PYTF')
