import hashlib
from typing import Optional
from pathlib import Path

def get_file_hash(path: Path) -> Optional[str]:
    try:
        with path.open("rb") as f:
            digest = hashlib.sha512(f.read())
        return digest.hexdigest()
    except FileNotFoundError:
        return None
