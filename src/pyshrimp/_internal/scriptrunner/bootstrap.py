import dataclasses
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback

import pkg_resources

from pyshrimp._internal.scriptrunner.cli import _handle_cli_maybe
from pyshrimp.utils.locking import acquire_file_lock


def _running_in_dev_mode():
    import pyshrimp._internal as pyshrimp_internal
    # the internal path will be in .../src/pyshrimp/_internal/__init__.py when running in dev mode
    pyshrimp_location = os.path.dirname(pyshrimp_internal.__file__).split(os.sep)[-3]
    return pyshrimp_location == 'src'


@dataclasses.dataclass
class _EnvConfig:
    log_enabled: bool
    cache_dir: str


def _default_env_config():
    _TRUE_VALUES = ['1', 'true', 'yes']
    return _EnvConfig(
        log_enabled=os.environ.get('PYSHRIMP_LOG', '0').lower() in _TRUE_VALUES,
        cache_dir=os.path.abspath(os.environ.get('PYSHRIMP_CACHE_DIR', None) or os.path.expanduser('~/.cache/pyshrimp'))
    )


class _ScriptConfig:

    def __init__(self):
        self.wrapper_opts_raw = []
        self.wrapper_opts = {}
        self.requirements = []


# noinspection PyMethodMayBeStatic
class _ScriptRunnerBootstrap:

    def __init__(self, env_config: _EnvConfig = None):
        env_config = env_config or _default_env_config()
        self._log_enabled = env_config.log_enabled
        self._cache_dir = env_config.cache_dir
        self._venvs_dir = os.path.join(self._cache_dir, 'virtual_envs')

    # -- Logging etc

    def log(self, message: str, level: str = 'INFO'):
        if self._log_enabled or level == 'ERROR':
            print(f'[PyShrimp:bootstrap] {level}: ' + message, file=sys.stderr)

    def log_error(self, message: str):
        self.log(message, 'ERROR')

    def exit_error(self, message: str, exit_code=1, exc_info=False):
        if exc_info:
            traceback.print_exc()

        self.log_error(message)

        raise sys.exit(exit_code)

    # -- script config parsing

    def parse_key_value_opts(self, line: str, pattern: str):
        result = {}
        opts_list = self.parse_list_opts(line, pattern)
        for el in opts_list:
            kv = el.split('=', maxsplit=1)
            if len(kv) == 1:
                result[kv[0]] = 'true'
            else:
                result[kv[0]] = kv[1]

        return result

    def parse_list_opts(self, line: str, pattern: str):
        m = re.match(pattern, line.strip())
        if not m:
            raise self.exit_error(f'Failed to parse config line: {line.strip()!r}')

        parsed = [el.strip() for el in m.group(1).split(',')]
        return [el for el in parsed if el]

    def read_script_config(self, target_script) -> _ScriptConfig:
        config = _ScriptConfig()

        if _running_in_dev_mode():
            config.requirements += [
                # for local testing use the dev install approach
                '-e', os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__), '../../../../'
                    )
                )
            ]
        else:
            config.requirements += [
                # in dist mode install version from pip, not older than the current one
                f'pyshrimp>={pkg_resources.get_distribution("pyshrimp").version}'
            ]

        with open(target_script, 'r') as f:
            for line in f:
                if not line.startswith('#'):
                    break

                # TODO: support for selecting base python (# $python: path) or/and maybe pyenv support...

                if line.startswith('# $opts:'):
                    config.wrapper_opts.update(
                        self.parse_key_value_opts(line, r'# \$opts:(.*)')
                    )
                    config.wrapper_opts_raw.append(line)

                elif line.startswith('# $requires:'):
                    config.requirements += self.parse_list_opts(line, r'# \$requires:(.*)')

        return config

    def validate_config(self, config: _ScriptConfig):
        valid = True
        if config.wrapper_opts.get('magic') != 'true':
            # magic is not active
            if config.wrapper_opts.get('devloop') == 'true':
                valid = False
                self.log_error('Detected invalid configuration - devloop is enabled but magic is not, this will not work as expected.')
                self.log_error('Possible solutions')
                self.log_error(' * remove devloop from $opts if you do not want the devloop')
                self.log_error(' * remove devloop from $opts and use run(main, devloop=True) instead')
                self.log_error(' * add magic to $opts - the power of magic will be with you')

            if config.wrapper_opts.get('elevate') == 'true':
                valid = False
                self.log_error('Detected invalid configuration - elevate is enabled but magic is not, this will not work as expected.')
                self.log_error('Possible solutions')
                self.log_error(' * remove elevate from $opts if you do not want the elevate option')
                self.log_error(' * remove elevate from $opts and use run(main, elevate=True) instead')
                self.log_error(' * add magic to $opts - the power of magic will be with you')

        if not valid:
            self.log_error('Script opts lines:')
            for line in config.wrapper_opts_raw:
                self.log_error(f' > {line.rstrip()}')

        return valid

    # -- virtual environment

    def can_use_venv(self):
        # noinspection PyBroadException
        try:
            import venv
            import ensurepip
            return True
        except Exception:
            return False

    def can_use_virtualenv(self):
        # noinspection PyBroadException
        try:
            # noinspection PyUnresolvedReferences
            import virtualenv
            return True
        except Exception:
            return False

    def prepare_virtualenv(self, config: _ScriptConfig):
        requirements = config.requirements
        requirements_hash = hashlib.sha1(':'.join(requirements).encode('utf-8')).hexdigest()
        self.log(f'Using requirements {requirements_hash}: {requirements}')
        venv_dir = os.path.join(self._venvs_dir, requirements_hash)
        setup_complete_marker_file = os.path.join(venv_dir, '.setup_completed')
        if not os.path.exists(setup_complete_marker_file):
            # create directory first so we can create lock file inside
            if not os.path.exists(venv_dir):
                os.makedirs(
                    venv_dir,
                    exist_ok=True  # it may exists due to race condition
                )

            # create lock outside of virtualenv directory as we will clear it
            setup_lock_file = os.path.join(self._venvs_dir, f'.setup_lock_{requirements_hash}')
            # TODO: consider some timed re-try logic in case of lock failure...
            with acquire_file_lock(setup_lock_file) as locked:
                if not locked:
                    raise self.exit_error(
                        f'Failed to setup virtualenv!'
                        f' Could not obtain lock under {setup_lock_file}.'
                        f' Are two scripts running the environment setup?',
                        exc_info=True
                    )

                self.log(f'Setting up venv: {venv_dir}')

                if self.can_use_venv():
                    self.setup_virtual_env_using_venv(venv_dir)

                elif self.can_use_virtualenv():
                    self.setup_virtual_env_using_virtualenv(venv_dir)

                else:
                    raise self.exit_error('Failed to setup virtual environment - cannot use venv or virtualenv!')

                if any((req.startswith('-e ') or req == '-e') for req in requirements):
                    # editable mode requested, we need to ensure that pip is fresh enough to support this
                    # solution to: '''A "pyproject.toml" file was found, but editable mode currently requires a setup.py based build.'''
                    self.log(f'Ensuring PIP is in fresh enough version to support editable requirements...')
                    pip_upgrade_result = subprocess.run(
                        [
                            os.path.join(venv_dir, 'bin/pip'), 'install', 'pip>=21.2.4'
                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    if pip_upgrade_result.returncode != 0:
                        raise self.exit_error(
                            f'Failed to upgrade pip!\n'
                            f'Upgrade output:\n'
                            f'{pip_upgrade_result.stdout}\n'
                            f'Error Output:\n'
                            f'{pip_upgrade_result.stderr}',
                            exc_info=True
                        )

                install_requirements_command = [os.path.join(venv_dir, 'bin/pip'), 'install'] + requirements
                self.log(f'Installing requirements: {install_requirements_command}')
                pip_install_result = subprocess.run(install_requirements_command, stdout=subprocess.PIPE)

                if pip_install_result.returncode != 0:
                    raise self.exit_error(
                        f'Failed to install requirements in virtualenv! Installation output:\n'
                        f'{pip_install_result.stdout}',
                        exc_info=True
                    )

                with open(setup_complete_marker_file, 'w') as f:
                    f.write(f'Completed at: {datetime.datetime.now().isoformat()}')

                self.log(f'Virtual env ready')

        python_executable = os.path.join(venv_dir, 'bin/python')
        return python_executable

    def setup_virtual_env_using_venv(self, venv_dir):
        import venv
        try:
            venv.create(venv_dir, system_site_packages=True, with_pip=True, clear=True)
        except BaseException:
            raise self.exit_error(f'Failed to setup virtualenv! Check previous messages for details.', exc_info=True)

    def setup_virtual_env_using_virtualenv(self, venv_dir):
        command = [sys.executable, '-m', 'virtualenv', '-p', sys.executable, '--clear', venv_dir]
        result = subprocess.run(command, stdout=subprocess.PIPE)
        if result.returncode != 0:
            raise self.exit_error(
                f'Failed to setup virtualenv!\n'
                f'Setup command: {command}'
                f'Setup output: {result.stdout}'
            )

    def execute_bootstrap(self):
        argv = sys.argv
        if len(argv) < 2:
            self.exit_error(f'Not enough arguments provided: {argv}')

        target_script = argv[1]
        args = argv[2:]

        self.log(f'target: {target_script}')
        self.log(f'args: {args}')

        if not os.path.exists(target_script) or not os.path.isfile(target_script):
            self.exit_error(
                f'Target script does not exist: {target_script}\n'
                f'Usage: pyshrimp target-script.py arg1 arg2 ... argN\n'
                f'For CLI options run: pyshrimp --help'
            )

        config = self.read_script_config(target_script)
        if not self.validate_config(config):
            raise self.exit_error('Script configuration is invalid, please see previous messages.')

        python_executable = self.prepare_virtualenv(config)

        if config.wrapper_opts.get('magic') == 'true':
            os.environ['PYSHRIMP_MAGIC_WRAPPER_OPTS'] = json.dumps(config.wrapper_opts)
            exec_args = [python_executable, '-u', '-m', 'pyshrimp._internal.wrapper.magicwrapper', '--', target_script] + args
        else:
            exec_args = [python_executable, '-u', target_script] + args

        self.log(f'Executing the script: {exec_args}')
        os.execlp(exec_args[0], *exec_args)


def _bootstrap():
    if _handle_cli_maybe():
        return
    else:
        _ScriptRunnerBootstrap().execute_bootstrap()
