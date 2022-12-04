import platform

_system_id = platform.system().lower()

def running_on_windows():
    return _system_id == 'windows'