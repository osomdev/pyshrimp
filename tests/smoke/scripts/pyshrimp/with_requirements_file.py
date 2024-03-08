#!/usr/bin/env pyshrimp
# $requirements_file: with_requirements_file.requirements1.txt
# $requirementsFile: with_requirements_file.requirements2.txt
# $requires_file: with_requirements_file.requirements3.txt
# $requiresFile: with_requirements_file.requirements4.txt

import click
import yaml
import jmespath
import numpy


@click.command()
def cli():
    modules_versions = ', '.join([f'{m.__name__}=={m.__version__}' for m in [click, yaml, jmespath, numpy]])
    print(f'We have modules from external file: {modules_versions}')


if __name__ == '__main__':
    cli()
