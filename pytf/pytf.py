#!/usr/bin/env python3

import sys

import click

from model.config import Config


@click.group()
@click.option('--log_dir', help='Log Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--family_dir', help='Family Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--job_dir', help='Job Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--instructions_dir', help='Instructions Directory',
              type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--run_wrapper', help='Run Wrapper', type=click.Path(file_okay=True, dir_okay=False, exists=True))
@click.option('--config_file', help="Config File", type=click.File('r'))
@click.pass_context
def pytf(context,
         log_dir,
         family_dir,
         job_dir,
         instructions_dir,
         run_wrapper,
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
    config.run_wrapper = run_wrapper if run_wrapper is not None else config.run_wrapper


@pytf.command()
@click.pass_context
def run(context):
    print(sys.path)


@pytf.command()
@click.argument('family')
@click.argument('job')
@click.pass_context
def rerun(context, family, job):
    config = context.obj['config']
    click.echo(config)
    click.echo(family)
    click.echo(job)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.argument('--error_code', type=click.IntRange(min=0, max=255))
@click.pass_context
def mark(context, family, job, error_code):
    config = context.obj['config']
    click.echo(config)
    click.echo(family)
    click.echo(job)
    click.echo(error_code)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.pass_context
def hold(context, family, job):
    config = context.obj['config']
    click.echo(config)
    click.echo(family)
    click.echo(job)


@pytf.command()
@click.argument('--family')
@click.argument('--job')
@click.pass_context
def release_hold(context, family, job):
    config = context.obj['config']
    click.echo(config)
    click.echo(family)
    click.echo(job)


if __name__ == '__main__':
    pytf(obj={}, auto_envvar_prefix='PYTF')
