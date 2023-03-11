#!/usr/bin/env pyshrimp
# $requirements_file: with_requirements_file.requirements.txt

import click
from click import secho


@click.command()
@click.pass_context
def cli(ctx):
    ctx.color = True
    secho('Click is with us and it was required from external file!', fg='green')


if __name__ == '__main__':
    cli()
