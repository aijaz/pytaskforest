import click


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
        config_file):
    print(f"{log_dir=}")
    print(f"{family_dir=}")
    print(f"{job_dir=}")
    print(f"{instructions_dir=}")
    print(f"{run_wrapper=}")
    print(f"{config_file=}")
    context.obj['config_file'] = config_file


@pytf.command()
@click.pass_context
def run(context):
    if config_file := context.obj['config_file']:
        f = config_file.read()
        print(f)


if __name__ == '__main__':
    pytf(obj={}, auto_envvar_prefix='PYTF')
