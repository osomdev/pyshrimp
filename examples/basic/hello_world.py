#!/usr/bin/env pyshrimp

from pyshrimp import run, log, shell_cmd

print('You can run this as any other script')
print('But then what is the point? :)')


def main():
    log('You can use log with a bit more details!')
    log('The log is initialized by run so do not forget about that.')
    log('You could use magic to simplify the script - see hello_world_with_magic.py')

    shell_cmd('echo You can also run shell scripts easily', capture=False).exec()


run(main)
