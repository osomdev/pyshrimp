#!/usr/bin/env pyshrimp
# $requires: click==7.0.0, requests, beautifulsoup4
import os
import re
import shutil
import sys

import click
import requests
from bs4 import BeautifulSoup
from click import confirm, style

from pyshrimp import run, log, shell_cmd, StringWrapper, exit_error, wait_until


def log_s(msg, fg=None, bold=None):
    log(style(msg, fg=fg, bold=bold))


def shell(cmd):
    log_s(f'Running: {cmd}', fg='blue')
    shell_cmd(cmd, capture=False, check=True).exec()


def pre_release_test():
    log_s('Preparing for tests execution...', bold=True, fg='blue')
    shell('docker build -t pyshrimp_docker .')

    log_s('Running unit tests', bold=True, fg='blue')
    shell('docker run -t pyshrimp_docker pytest tests/unit')

    log_s('Running smoke tests', bold=True, fg='blue')
    shell('docker run -t pyshrimp_docker pytest tests/smoke')

    log_s('All tests passed', bold=True, fg='green')


def post_release_test(release_version, target_env):
    log_s('Preparing for post release test execution...', bold=True, fg='blue')
    shell('docker build -t pyshrimp_post_release_test docker/post_release_test')

    pypi_repo = 'https://test.pypi.org/simple' if target_env == 'staging' else 'https://pypi.org/simple'
    wait_until(
        'Module is available for download...',
        collect=lambda: release_exists('pyshrimp', release_version, pypi_repo),
        timeout_sec=60,
        check_interval_sec=1,
        before_sleep=lambda res: log_s(' * Still not available...'),
        on_timeout=lambda res: log_s('Module is still not available, test will probably fail', fg='yellow', bold=True)
    )

    log_s('Running post release test...', bold=True, fg='blue')
    shell(f'docker run -t pyshrimp_post_release_test ./run-post-release-test.sh "{release_version}" "{target_env}"')


def release_exists(module, version, repository):
    res = requests.get(f'{repository.rstrip("/")}/{module}')
    if res.status_code != 200:
        return False

    for link in BeautifulSoup(res.text, 'html.parser').find_all('a'):
        if re.match(f'{module}-{version}-py3.*', link.get_text()):
            return True

    return False


@click.command()
@click.option('--skip-tests', 'skip_tests', is_flag=True, help='Skips tests execution', default=False)
@click.option('--stg/--no-stg', 'deploy_to_staging', is_flag=True, help='Performs staging deploy', default=None)
@click.option('--prod/--no-prod', 'deploy_to_prod', is_flag=True, help='Performs production deploy', default=None)
@click.option('--do-not-ask', 'skip_questions', is_flag=True, help='Do not ask for confirmation')
@click.option('--skip-post-release-verification', 'skip_post_release_verification', is_flag=True, help='Skips posts release verification', default=False)
def main(skip_tests, deploy_to_staging, deploy_to_prod, skip_questions, skip_post_release_verification):
    # ensure that path is set to root directory of the project
    os.chdir(os.path.dirname(os.path.dirname(__file__)))

    if not os.path.exists('setup.cfg'):
        exit_error(f'Could not find the setup.cfg - was the script moved? cwd={os.getcwd()}')

    version = _get_release_version()

    if skip_questions and (deploy_to_staging is None or deploy_to_prod is None):
        raise exit_error('Illegal arguments - you must decide if you want to use prod and staging deployment when using do not ask option.')

    if skip_questions:
        log(f'Preparing to release version {version}')
    else:
        confirm(f'Will release version {version}. Are you sure?', abort=True)

    shutil.rmtree('./dist/', ignore_errors=True)
    shell('python3 -m build --help 2>/dev/null >/dev/null || python3 -m pip install --upgrade build')
    shell('python3 -m build')
    shell('python3 -m twine --help 2>/dev/null >/dev/null || python3 -m pip install --upgrade twine')

    # ~~ pre-release tests

    if skip_tests:
        log('Skipping tests execution.')
    else:
        pre_release_test()

    # ~~ staging deployment

    if deploy_to_staging is False:
        pass

    elif (deploy_to_staging and skip_questions) or confirm(f'Should I deploy to staging?'):
        shell('python3 -m twine upload --repository testpypi dist/*')

        if skip_post_release_verification:
            log('Skipping post release verification [staging]')
        else:
            log('Running post release verification [staging]')
            post_release_test(version, 'staging')

    # ~~ production deployment

    if deploy_to_prod is False:
        pass

    elif (deploy_to_prod and skip_questions) or confirm(f'Should I deploy to production?'):
        shell('python3 -m twine upload dist/*')

        if skip_post_release_verification:
            log('Skipping post release verification [production]')
        else:
            log('Running post release verification [production]')
            post_release_test(version, 'production')

    log_s('All done.', fg='green', bold=True)


def _get_release_version():
    with open('src/pyshrimp/__init__.py') as f:
        version = StringWrapper(f.read()).match_lines(r"__version__ = '(.*)'")[0]
    return version


try:
    run(main)
except click.exceptions.Abort:
    log('Aborted.')
    sys.exit(1)
