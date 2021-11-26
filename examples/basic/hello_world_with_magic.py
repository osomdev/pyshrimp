#!/usr/bin/env pyshrimp
# $opts: magic

from pyshrimp import log, shell_cmd

print('You can run this as any other script')
print('But then what is the point? :)')

log('You can use log with a bit more details!')
log('The log is initialized by run... but with magic it gets magically invoked!')
log('To do that just add magic to opts: # $opts: magic')
log('The downside is: script will run differently when invoked directly using %> python script.py')
log('Also if you forget to turn on magic those logs will not appear...')

shell_cmd('echo You can also run shell scripts easily', capture=False).exec()
