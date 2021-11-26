#!/usr/bin/env pyshrimp
# $requires: click==7.0

import click
from click import secho


@click.command()
@click.pass_context
def cli(ctx):
    ctx.color = True
    secho('Click is with us!', fg='green')


if __name__ == '__main__':
    cli()
