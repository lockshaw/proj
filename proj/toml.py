try:
    from tomllib import loads, TOMLDecodeError 
except ImportError:
    from toml import loads, TOMLDecodeError
