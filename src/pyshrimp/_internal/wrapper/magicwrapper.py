import json
import os
import sys

from pyshrimp import run
from pyshrimp._internal.wrapper.magicwrapper_state import _MAGIC_STATE


def _split_items_by(items, separator_element):
    left = []
    right = []
    separator_found = False
    for el in items:
        if separator_found:
            right.append(el)

        elif el == separator_element:
            separator_found = True

        else:
            left.append(el)

    return left, right


def main():
    opts = json.loads(os.environ.get('PYSHRIMP_MAGIC_WRAPPER_OPTS', '{}'))

    original_args = sys.argv
    wrapper_args, program_args = _split_items_by(original_args[1:], '--')
    program_file = program_args[0]
    sys.argv = program_args.copy()

    _MAGIC_STATE.active = True

    def _re_run_script():
        args = [sys.executable] + original_args
        os.execlp(args[0], *args)

    # initialize
    def _script():
        # load script
        import importlib.util
        module_spec = importlib.util.spec_from_file_location("__main__", program_file)
        module_ref = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module_ref)

    run(
        script=_script,
        check_main=False,
        devloop=opts.get('devloop') == 'true',
        elevate=opts.get('elevate') == 'true',
        re_run_script=_re_run_script,
        script_path=program_file
    )


if __name__ == '__main__':
    main()
