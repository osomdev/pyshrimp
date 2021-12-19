#!/bin/bash

set -e

pyshrimp_version="$1"
target_env="$2"

# install PyShrimp
if [[ "$target_env" == "production" ]]; then
  pip install "pyshrimp==$pyshrimp_version"

elif [[ "$target_env" == "staging" ]]; then
  pip install --index-url https://test.pypi.org/simple/ --no-deps "pyshrimp==$pyshrimp_version"

else
  echo "Unknown target environment: $target_env"
  exit 1

fi

# help should not fail
pyshrimp --help

# new script creation should work
pyshrimp new new-script.py
ls -ls new-script.py
echo "== NEW SCRIPT:"
cat new-script.py
echo "---"

if [[ "$target_env" == "production" ]]; then
  # verification script should run fine
  ./verify-release-script.py
else
  echo "SKIP: Not attempting script execution as it will fail to install PyShrimp outside of production environment"
fi