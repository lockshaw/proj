import argparse
import logging
from typing import (
    Any, 
    List,
)
import sys
from enum import Enum

def add_verbosity_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("-v", "--verbose", action="count", default=0)
    p.add_argument("-q", "--quiet", action="count", default=0)
    p.add_argument("--silent", action="store_true")
    p.set_defaults(supports_verbosity=True)

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    SILENT = logging.CRITICAL + 1


def calculate_log_level(args: Any) -> int:
    LEVELS: List[LogLevel]  = [
        LogLevel.DEBUG,
        LogLevel.INFO,
        LogLevel.WARN,
        LogLevel.ERROR,
        LogLevel.CRITICAL,
        LogLevel.SILENT,
    ]
    default_verbosity = LEVELS.index(LogLevel.WARN)
    if not (hasattr(args, 'supports_verbosity') and args.supports_verbosity):
        return default_verbosity

    verbosity: int = min(max(args.quiet - args.verbose + default_verbosity, 0), len(LEVELS)-1)

    max_verbosity = len(LEVELS) - 1
    level = LEVELS[verbosity]

    if level != LogLevel.SILENT:
        print(f'Verbosity set to ({max_verbosity - verbosity}/{max_verbosity})', file=sys.stderr)

    setattr(args, 'verbosity', level.value)

    return level.value
