import os.path
import stat
import sys
import textwrap

# noinspection PyProtectedMember
from pyshrimp._internal.utils.errors import _exit_error


def _dedent(content: str):
    return textwrap.dedent(
        content.strip('\n')
    )


def print_multiline(content: str):
    print(_dedent(content))


# noinspection PyUnusedLocal
def _cmd_help(cmd, args):
    print_multiline(
        '''
        The pyshrimp is wrapper tool for python scripts.
        
        Usages:
        
        1) pyshrimp [target-script.py] [arg]...
        
        Executes target script with PyShrimp. This is also used in case of she-bang in script.
        Arguments will be passed to the target script as standard arguments.
        
        2) pyshrimp [command] [arg]...
        
        Executes CLI command.
        
        COMMANDS:
        
            [help|--help]  
                Prints this message
                
            [generate|new] [new-script-name.py]
                Creates new script.
                If the new script name is not provided prints the script to standard output.  
                
        ENVIRONMENT VARIABLES:
        
            PYSHRIMP_LOG - if set to 1 the bootstrap process will provide additional diagnostic output
            PYSHRIMP_CACHE_DIR - location of cache directory for PyShrimp (default: ~/.cache/pyshrimp) 
            
        '''
    )


def _cmd_generate(cmd, args):
    if len(args) > 1:
        raise _exit_error(f'Too many arguments provided for `{cmd}`: {" ".join(args)}')

    script_content = _dedent(
        '''
        #!/usr/bin/env pyshrimp
        # $requires: 
        
        from pyshrimp import run, log
        
        
        def main():
            log('Hello world, this script uses devloop!')
        
            
        run(main, devloop=True)
        '''
    )

    if args:
        new_script_path = os.path.abspath(args[0])
        if os.path.exists(new_script_path):
            raise _exit_error(
                f'Target script exists, refusing to override. '
                f'Please provide non existing file name. '
                f'Provided name resolved to: {new_script_path}'
            )

        print(f'Writing content to new script: {new_script_path}')

        with open(new_script_path, 'w') as f:
            f.write(script_content)

        # make the script writable
        st = os.stat(new_script_path)
        os.chmod(new_script_path, st.st_mode | stat.S_IEXEC)

    else:
        print(script_content)


_commands = {
    '--help': _cmd_help,
    'help': _cmd_help,
    '-help': _cmd_help,
    'generate': _cmd_generate,
    'new': _cmd_generate
}


def _handle_cli_maybe() -> bool:
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:]

        handler = _commands.get(command)
        if handler:
            handler(command, args)
            return True

    return False
