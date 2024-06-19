import re

import tomlkit.items

import pytf.exceptions as ex

def parse_time(d, field_parent_name, field_name, exception_str) -> (int | None, int | None):
    if val := d.get(field_name):
        if len(val) != 4:
            raise ex.PyTaskforestParseException(f"{exception_str} {field_parent_name}")
        try:
            hh, mm = (int(val[:2]), int(val[2:]))
        except ValueError as e:
            raise ex.PyTaskforestParseException(
                f"{exception_str} {field_parent_name}"
            ) from e
        return hh, mm

    return None, None


def lower_true_false(line: str) -> str:
    patterns = ((re.compile('(= *)TRUE\\b', flags=re.IGNORECASE), '= true'),
                    (re.compile('(= *)FALSE\\b', flags=re.IGNORECASE), '= false'))
    for pattern, repl in patterns:
        line = re.sub(pattern, repl, line)

    return line


def simple_type(obj) -> str:
    if type(obj) is tomlkit.items.String:
        return 'str'
    elif type(obj) is tomlkit.items.Integer:
        return 'int'
    elif type(obj) is bool:
        return 'bool'
    else:
        return type(obj)
