from pathlib import Path
from . import subprocess_trace as subprocess
import os
from typing import (
    Optional,
)

def open_in_browser(p: os.PathLike, cwd: Optional[Path] = None) -> None:
    subprocess.run(
        [
            "xdg-open",
            os.fspath(p)
        ],
        cwd=cwd,
        env=os.environ,
    )
