import click


@click.group()
@click.option('--log_dir', help='Log Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--family_dir', help='Family Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--job_dir', help='Job Directory', type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--instructions_dir', help='Instructions Directory',
              type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option('--run_wrapper', help='Run Wrapper', type=click.Path(file_okay=True, dir_okay=False, exists=True))
# @click.option('--wait_time', help='Wait Time', type=click.INT)
# @click.option('--end_time_hr', help='End Time HH', type=click.IntRange(min=0, max=23))
# @click.option('--end_time_min', help='End Time MIN', type=click.IntRange(min=0, max=59))
# @click.option('--collapsed', help='Collapsed', type=click.BOOL)
# @click.option('--chained', help='Chained', type=click.BOOL)
# @click.option('--log_level', help='Log Level', type=click.INT)  # TODO: Convert from string to type
# @click.option('--ignore_regex', help='Ignore Regex', multiple=True)
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
