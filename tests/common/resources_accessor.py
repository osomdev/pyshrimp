import os


def get_test_resource_file_path(file_name):
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'resources',
            file_name
        )
    )


def get_test_resource_file_as_text(file_name):
    file_path = get_test_resource_file_path(file_name)
    with open(file_path, 'r') as f:
        return file_path, f.read()


def get_test_resource_file_as_bytes(file_name):
    file_path = get_test_resource_file_path(file_name)
    with open(file_path, 'rb') as f:
        return file_path, f.read()
