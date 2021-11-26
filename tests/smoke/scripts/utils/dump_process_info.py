#!/usr/bin/env python
import json
import os
import sys

data = {
    'argv': sys.argv,
    'env': os.environ.copy()
}
print(f'PROCESS INFO:{json.dumps(data)}')
