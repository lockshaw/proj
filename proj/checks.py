from enum import StrEnum
from .config_file import ProjectConfig
from .format import run_formatter_check

class Check(StrEnum):
    FORMAT = 'format'

def run_check(config: ProjectConfig, check: Check) -> None:
    assert check == Check.FORMAT
    return run_formatter_check(config)
