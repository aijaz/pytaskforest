import tomlkit

from pytf.parse_utils import simple_type


def test_simple_type():
    doc = tomlkit.parse('a = "A"')
    assert simple_type(doc['a']) == 'str'
    doc = tomlkit.parse('a = 1')
    assert simple_type(doc['a']) == 'int'
    doc = tomlkit.parse('a = true')
    assert simple_type(doc['a']) == 'bool'
    doc = tomlkit.parse('a = [1, 2, 3]')
    assert simple_type(doc['a']) == type(doc['a'])
