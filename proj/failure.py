import sys
import logging

_l = logging.getLogger(__name__)

def fail_with_error(err: str, error_code: int = 1) -> None:
    _l.error(err)
    sys.exit(error_code)
