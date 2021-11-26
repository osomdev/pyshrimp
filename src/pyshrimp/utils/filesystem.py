import os
from glob import glob

from pyshrimp.exception import IllegalArgumentException


def _ls(list_supplier, dirs_only=False, files_only=False):
    if dirs_only and files_only:
        raise IllegalArgumentException('Illegal arguments - dirs_only and files_only cannot be true together')

    full_paths = [
        # remove trailing separator, but don't do that if the whole string is trailing separator
        # just in case someone actually uses /** which should return the /
        path.rstrip(os.path.sep) if path != os.path.sep else path for path in list_supplier()
    ]

    if dirs_only or files_only:
        return list(
            filter(
                os.path.isdir if dirs_only else os.path.isfile,
                full_paths
            )
        )
    else:
        # no filtering required
        return full_paths


def ls(*path_segments: str, dirs_only=False, files_only=False):
    path = os.path.join(*path_segments)
    return _ls(
        lambda: [
            os.path.join(path, file_name) for file_name in os.listdir(path)
        ],
        dirs_only=dirs_only,
        files_only=files_only
    )


def glob_ls(*path_glob_segments: str, dirs_only=False, files_only=False, recursive=False):
    return _ls(
        lambda: glob(os.path.join(*path_glob_segments), recursive=recursive),
        dirs_only=dirs_only,
        files_only=files_only
    )
