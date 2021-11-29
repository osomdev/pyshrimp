import os
from glob import glob
from typing import AnyStr

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


def write_to_file(file_path: str, data: AnyStr, open_mode='w') -> None:
    with open(file_path, open_mode) as f:
        f.write(data)


def read_file(file_path: str) -> str:
    """
    Read contents of file using text mode.

    :param file_path:
    :return:
    """
    with open(file_path, 'r') as f:
        return f.read()


def read_file_bin(file_path: str) -> bytes:
    """
    Read contents of file using binary mode.

    :param file_path:
    :return:
    """
    with open(file_path, 'rb') as f:
        return f.read()


def chmod_set(file_path, mode_to_set) -> None:
    """
    Updates file mode with given flags (new_mode = current_mode | mode_to_set)

    :param file_path: Path of the target file
    :param mode_to_set: Flags to set, see stat.S_* for values
    :return:
    """
    st = os.stat(file_path)
    os.chmod(file_path, st.st_mode | mode_to_set)


def chmod_unset(file_path, mode_to_remove) -> None:
    """
    Updates file mode by removing given flags (`new_mode = current_mode ^ mode_to_remove`)

    :param file_path: Path of the target file
    :param mode_to_remove: Flags to remove, see stat.S_I* for values
    :return:
    """
    st = os.stat(file_path)
    os.chmod(file_path, st.st_mode ^ mode_to_remove)
