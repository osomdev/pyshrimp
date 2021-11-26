# Building the project

Following the https://packaging.python.org/tutorials/packaging-projects/

## Building

```shell
# install build tool
python3 -m pip install --upgrade build

# build
python3 -m build
```

## Publishing

```shell
# install twine
python3 -m pip install --upgrade twine

# upload to test repository
python3 -m twine upload --repository testpypi dist/*

# upload to production repository
python3 -m twine upload --repository dist/*
```

## Testing package

```shell
# install package from test repository
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps pyshrimp
```