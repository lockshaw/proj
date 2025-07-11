from pathlib import Path
from . import subprocess_trace as subprocess
import os
from typing import (
    Optional,
    Union,
)


def open_in_browser(p: Union[str, Path], cwd: Optional[Path] = None) -> None:
    _p = Path(p)
    subprocess.run(
        [
            "xdg-open",
            str(_p),
        ],
        cwd=cwd,
        env=os.environ,
    )
