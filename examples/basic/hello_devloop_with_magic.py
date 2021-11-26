#!/usr/bin/env pyshrimp
# $opts: magic,devloop
from pyshrimp import log

log('Hello devloop!')
log('When you run this script it will execute and wait for change.')
log('Once the script is modified it should automatically re-run.')
log('As this script runs with magic we do not need to invoke the run manually.')
log('The downside is that this script will behave differently when run with python directly.')
