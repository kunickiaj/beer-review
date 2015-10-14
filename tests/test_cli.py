import pytest
from click.testing import CliRunner
from beer import cli


@pytest.fixture
def runner():
    return CliRunner()


