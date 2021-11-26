from dataclasses import dataclass
from typing import Any, List, Tuple

_dot_dict_state_field_name = '_DotDict__dot_dict_state_d40de1e455ae'


def _format_path(path):
    res = []

    for idx, (el_name, sep) in enumerate(path):
        if idx > 0:
            res.append(sep)

        res.append(el_name)

    return ''.join(res)


@dataclass
class _DotDictState:
    data: Any
    path: List[Tuple[str, str]]


def _map_item(dot_dict, p, v):
    if isinstance(v, dict):
        return DotDict(
            data=v,
            path=getattr(dot_dict, _dot_dict_state_field_name).path + p
        )

    elif isinstance(v, list):
        return [_map_item(dot_dict, p + [(f'[{idx}]', '')], el) for idx, el in enumerate(v)]

    else:
        return v


class DotDict:
    """
    Dict wrapper class designed to enable property-like access to dictionary elements.

    Example:

            >>> d = DotDict(original_dict)
            >>> print(d.a.b.c)

    """

    def __init__(self, data, path=None):
        # use some weird name that have very low chance of colliding with actual key in target dict
        # the full version of this name must match the _dot_dict_state_field_name
        self.__dot_dict_state_d40de1e455ae = _DotDictState(
            data=data,
            path=path or []
        )

    def __getattr__(self, item):
        try:
            return _map_item(self, [(item, '.')], self.__dot_dict_state_d40de1e455ae.data[item])
        except KeyError:
            raise KeyError(_format_path(self.__dot_dict_state_d40de1e455ae.path + [(item, '.')]))

    def __setattr__(self, key, value):
        if key == _dot_dict_state_field_name:
            super().__setattr__(key, value)
        else:
            self.__dot_dict_state_d40de1e455ae.data[key] = value

    def __repr__(self):
        return repr(self.__dot_dict_state_d40de1e455ae.data)

    def __str__(self):
        return str(self.__dot_dict_state_d40de1e455ae.data)

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)


def as_dot_dict(dict_data, variable_name='dict'):
    return DotDict(dict_data, [(variable_name, '.')])
