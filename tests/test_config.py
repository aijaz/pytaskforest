import pytest

import pytf.exceptions as ex
from pytf.config import Config


def test_invalid_config_eof_raises_exception():
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        config_str = 'tz="America/Chicago'
        _ = Config.from_str(config_str)
    assert str(exc_info.value) == ex.MSG_CONFIG_PARSING_FAILED


def test_invalid_config_unexpected_char_raises_exception():
    with pytest.raises(ex.PyTaskforestParseException) as exc_info:
        config_str = 'tz="America/Chicago" a'
        _ = Config.from_str(config_str)
    assert str(exc_info.value) == ex.MSG_CONFIG_PARSING_FAILED
