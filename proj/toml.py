import sys

if sys.version_info[:2] >= (3, 11): 
    from tomllib import (
        loads as loads, 
        TOMLDecodeError as TOMLDecodeError,
    )
else:
    from toml import (
        loads as loads, 
        TOMLDecodeError as TOMLDecodeError,
    )
