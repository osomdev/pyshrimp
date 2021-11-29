# PyShrimp

<img src="https://osomdev.github.io/pyshrimp/assets/img/logo/pyshrimp_logo_transparent_250.png" align="right" alt="PyShrimp logo">

PyShrimp is combination of utilities designed to support easy creation of small python scripts instead of getting your
hands dirty with shell scripting languages like bash.

When trying to write simple script to hack some ad-hoc task it's easy to end up with following choices:

- use bash - it's easy to write simple script which invokes some processes. But then it's hard to do something more
  advanced (lacking good support for types, lacking support for arrays...)
- use python - is far better in handing different types, have good support for various collections, can easily be
  expanded by installing dependencies from pip. But then there is painful overhead in setting up such script
  (handling virtualenv to separate dependencies, or using one big env for all scripts) and doing more complex process
  invocations beyond simple `subprocess.check_output(...)` is also far from ideal.

The PyShrimp aims at solving this - it's purpose is to remove barriers so developers can use python for simple
shell-scripting purpose. No more over-grown bash scripts, no more pain with env setup or subprocess handling!

Note: the features provided are not expected to replace poetry and other tools like that - if you can afford the
complexity then it's probably better to use those ;). But for single-file scripts it should be way easier to go with
PyShrimp.

## TL;DR: Showcase

The rest of README explains features in detail. For those impatient there is quick example script - the code
is often worth 1000 words (although it covers only small subset of features):

```python
#!/usr/bin/env pyshrimp
# $opts: magic,devloop
# $requires: click==7.0,requests==2.22.0
import requests
from click import style

from pyshrimp import log, as_dot_dict


def slog(message, **kwargs):
    log(style(message, **kwargs))


slog('Loading issues...')

res = as_dot_dict(
    requests.get(
        'https://jira.atlassian.com/rest/api/2/search', params={
            'jql': 'created > -1d',
            'maxResults': '5'
        }
    ).json(),
    'res'
)

slog(f'Issues ({res.total} in total):', fg='green', bold=True)

for issue in res.issues:
    line_color = 'red' if issue.fields.issuetype.name == 'Bug' else None
    f = issue.fields
    slog(f' * [{issue.key}] [{f.issuetype.name}] [{f.status.name}] {f.summary}', fg=line_color)
```

To run this script you need to have the PyShrimp installed:

```shell
pip install pyshrimp
chmod +x thescript.py
./thescript.py
```

PyShrimp will automatically initialize new virtual environment, install dependencies declared in file header,
and execute the script with devloop:

![Showcase output](https://osomdev.github.io/pyshrimp/assets/img/pyshrimp_showcase_output.png)

## Features

### Virtual env setup - `$requires`

PyShrimp parses script header and looks for the `# $requires: ...` lines.
Each such line can contain one or more pip-style requirements, for example:

```python
#!/usr/bin/env pyshrimp
# $requires: click==7.0,requests==2.22.0
# $requires: PyYAML==5.3.1
```

Before script execution PyShrimp will create dedicated virtual env in `~/.cache/pyshrimp/{hash}/`
where `{hash}` is hash value from the requirements. The environment is created only once - subsequent
runs of script will use already existing environment. Scripts with exactly the same dependencies will
re-use single virtual environment.

### Creation of new script

To quickly create new script just run the `new` command:

```shell
pyshrimp new my-new-script.py
```

[![](https://osomdev.github.io/pyshrimp/assets/img/asciinema_script_creation_snapshot.png)](
  https://asciinema.org/a/9dDyBs1n1YkNtJBchFv3yZCt6?autoplay=1
)

The file created will contain skeleton of script. Script will have the executable mode set already.

### Script startup - `run`

The `run` function makes it easy to run the main function with some extra capabilities.
The default behavior is to set up logging and run the script main function.
In addition to this it's possible to enable additional tweaks:

* `devloop` - runs script in loop - PyShrimp will re-execute script automatically after it changes
* `elevate` - ensures that script is running as root - uses sudo to elevate permissions

Example script with both features enabled:

```python
#!/usr/bin/env pyshrimp
from pyshrimp import run, log


def main():
  log('Hello world!')


run(main, devloop=True, elevate=True)
```

### Power of magic

There is alternative 'magic' way to run script setup (logging configuration) and achieve the bonus features
like devloop and elevate. This is called magic as the PyShrimp no longer will only set up virtualenv but also
will wrap the code with extra "magical" setup.

The following script will have exactly the same behavior as previously presented with `run` method:

```python
#!/usr/bin/env pyshrimp
# $opts: magic,devloop,elevate
from pyshrimp import log

log('Hello world!')
```

As you can see there is less "boilerplate" code when using this approach.

There is however one downside - the code run with just `python` will behave differently - the magic options will not
activate and also the logging will be not configured. This can be surprising when running script with debugger so
use the magic wisely ;).

### Useful utilities

There are few useful utilities provided:

* `as_dot_dict` - creates dictionary wrapper with support for property-like access 
  to the values: `as_dot_dict(d).some_key.some_list[1].some_value`
* `unwrap_dot_dict` - un-wraps DotDicts back into the raw dict/list
* `ls`, `glob_ls` - lists files and directories
* `write_to_file`, `read_file`, `read_file_bin` - file content manipulation
* `chmod_set`, `chmod_unset` - sets/unsets file mode bits
* `acquire_file_lock`, `FileBasedLock` - handles file based locking
* `re_match_all` - runs regular expression matching across the list and returns selected 
  group from the matched elements
* `in_background` - runs function in background thread pool
* [`StringWrapper`](src/pyshrimp/utils/string_wrapper.py) - provides few methods especially useful for parsing process output
* `parse_table` - parses table-like output into `ParsedTable`
* `create_regex_splitter` - creates `regex_splitter` - useful to handle unusual table/column-like output
* `wait_until`, `wait_until_gen` - handles waiting for some result with timeout using periodic polling

You can see example usage in [examples](examples) and also in [tests](tests).

### Easily run programs - simple subprocess helper

The subprocess helper simplifies the task of running processes and handling the results.

```python
from pyshrimp import run_process
print(
  run_process('echo -n 123 | wc -c', run_in_shell=True).raise_if_not_ok().standard_output
)
```

### More advanced subprocess helper

The `cmd` and `shell_cmd` will produce `Command` object which can be executed with extra params:

```python
from pyshrimp import shell_cmd
wc_c = shell_cmd('echo -n "$1" | wc -c', check=True)
print(wc_c('123456789').standard_output.strip()) // 9
print(wc_c.exec('123').standard_output.strip()) // 3
```

It is worth noting here that standard_output and error_output
are [wrapped with `StringWrapper`](src/pyshrimp/utils/string_wrapper.py) to ease output parsing.

## Pipeline support

### Motivation

The nice property about bash scripts is how easy it is to executed process and pass the output between processes. It's
all possible in python but the overhead is really too big to use in small scripts. It's more convenient to fallback into
subprocess with partial shell script than glue together the processes directly in python code.

### Solution

The `ExecutionPipeline` is designed to address those concerns. You can easily stitch together few processes and
functions together to process the input and output just like in shell scripts.

There are two approaches - standard object-oriented python code and more shell like pipeline syntax.

### Object oriented usage

```python
from pyshrimp import ExecutionPipeline, cmd
p = ExecutionPipeline()
# feed pipeline with text input
p.attach_text('Hello world!')
# run the wc command
p.attach(cmd('wc'))
# run awk, using the shell wrapper
p.attach("awk '{print $3}'")
# process the output with function - pad with zeros
p.attach_function(
    lambda stdin: f'{int(stdin.strip()):05}'
)
# close pipeline and collect output
res = p.close().stdout
print(res) # 00012
```

### Shell-like pipe syntax

The shell-like syntax is "abusing" the python feature which allows overriding behavior of binary or operator. It's not
very elegant (could be confusing for people) but on the other hand this fits nicely the purpose - being easy replacement
of shell pipes.

```python
from pyshrimp import PIPE, PIPE_END_STDOUT, cmd
res = (
    # feed pipeline with text input
    PIPE.text('Hello world!')
    # run the wc command
    | cmd('wc')
    # run awk, using the shell wrapper
    | "awk '{print $3}'"
    # process the output with function - pad with zeros
    | (lambda stdin: f'{int(stdin.strip()):05}')
    # close pipeline and collect output
    | PIPE_END_STDOUT
)
print(res) # 00012
```

### Mixed approach

You can mix the shell-like and object-oriented syntax (if you have good reason to do so ;)). Under the cover
the `ExecutionPipeline` is being used even in the shell-like syntax.

```python
from pyshrimp import PIPE, cmd
p = (
    # feed pipeline with text input
    PIPE.text('Hello world!')
    # run the wc command
    | cmd('wc')
    # run awk, using the shell wrapper
    | "awk '{print $3}'"
)
# process the output with function - pad with zeros
p.attach_function(lambda stdin: f'{int(stdin.strip()):05}')
# close pipeline and collect output
res = p.close().stdout
print(res) # 00012
```

### Limitations

Things obviously missing in current version that you should be aware of:

- Limited error handling support
- Only text streams are officially supported, with UTF-8 hardcoded
- Only connection of standard output is supported - error output behavior is undetermined (most likely flows to stderr)

Those limitations can be addressed in future (if there is enough demand and willingness to introduce the change).

## Troubleshooting

### Diagnosing virtual env setup failure

You can set `PYSHRIMP_LOG` environment variable to `1` this will instruct boostrap code to
produce diagnostic messages:

```shell
% PYSHRIMP_LOG=1 ./show_recently_created_issues.py a b
[PyShrimp:bootstrap] INFO: target: ./show_recently_created_issues.py
[PyShrimp:bootstrap] INFO: args: ['a', 'b']
[PyShrimp:bootstrap] INFO: Using requirements d82e6efbb5ea5ba895b6fe103b4c50bf3ac75eb3: [
  'pyshrimp', 'click==7.0'
]
[PyShrimp:bootstrap] INFO: Executing the script: [
  '~/.cache/pyshrimp/virtual_envs/d82e6e.../bin/python', '-u', 
  '-m', 'pyshrimp._internal.wrapper.magicwrapper', 
  '--', './show_recently_created_issues.py', 'a', 'b'
]
  
Hello world
```

## Supported environment

This project was developed on **Ubuntu Linux**. It should work with any linux system, but I can imagine the tests
failing in case some system binaries are missing.

It was not tested on macOS (probably will work fine) and some parts for sure will not work on Windows
(e.g. shell wrapping is depending on bash).

Feel free to raise bugs found when using this project on macOS - it shouldn't be too hard to address them.

The author does not have plans to introduce support for Windows but contributions are welcome ;).

## License

The project is licensed under [MIT License](./LICENSE.txt) with exceptions listed below.

Project license exceptions:

1. The files in [doc/assets/img/logo](doc/assets/img/logo) and [docs/assets/img/logo](doc/assets/img/logo) directory
   are licensed under [CC BY-SA 3.0 license](https://creativecommons.org/licenses/by/3.0/legalcode).

## Contributions

Feel free to contribute to this project - I'll do my best to review and accept contributions.

Please include at least some happy-path tests for your changes.

## Imaginary Q&A

Q: Shouldn't this project be separated into few ones (e.g. pipelines, commands, script bootstrap)?  
A: Probably yes. And maybe it will be split in the future. But for now it's more convenient to manage single project.

## Credits

- The logo was created using ["Shrimp" icon](https://thenounproject.com/elabans/collection/seafood/?i=541402)
  created by ["elmars"](https://thenounproject.com/elabans/) and published 
  under [CC BY-SA 3.0 license](https://creativecommons.org/licenses/by/3.0/us/legalcode).