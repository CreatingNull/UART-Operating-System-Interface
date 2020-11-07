"""Unit tests for the web-app package functionality."""
from pathlib import Path

from uosinterface.util import load_config


def test_load_config():
    """Checks the configuration can be loaded successfully for the server."""
    config_bad = load_config(Path("Non-existent.ini"))
    config_good = load_config(
        Path(__file__)
        .resolve()
        .parents[3]
        .joinpath(Path("resources/UARTOSInterface.ini"))
    )
    assert config_bad is None
    assert config_good is not None