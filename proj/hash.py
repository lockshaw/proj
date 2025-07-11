import hashlib
from typing import Optional
from pathlib import Path


def get_file_hash(path: Path) -> Optional[bytes]:
    try:
        with path.open("rb") as f:
            digest = hashlib.md5(f.read())
        return digest.digest()
    except FileNotFoundError:
        return None
