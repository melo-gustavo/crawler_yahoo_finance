from unittest.mock import Mock

from drivers.base_driver import BaseDriver


def test_set_config_driver_adds_all_flags_without_headless():
    options = Mock()

    BaseDriver().set_config_driver(options, headless=False)

    added_args = [call.args[0] for call in options.add_argument.call_args_list]

    assert "--headless" not in added_args
    assert "--disable-gpu" in added_args
    assert "--disable-extensions" in added_args
    assert "--blink-settings=imagesEnabled=false" in added_args


def test_set_config_driver_adds_headless_when_enabled():
    options = Mock()

    BaseDriver().set_config_driver(options, headless=True)

    added_args = [call.args[0] for call in options.add_argument.call_args_list]
    assert "--headless" in added_args
