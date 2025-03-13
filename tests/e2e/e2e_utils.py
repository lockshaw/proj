from pathlib import Path
import subprocess
from typing import (
    Iterable,
)
import os

def require_successful(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    assert r.returncode == 0, r.stderr
    return r

def require_fail(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    assert r.returncode != 0
    return r

def run(dir: Path, args: Iterable[str], capture: bool = True) -> subprocess.CompletedProcess:
    cmd = [
        'proj',
        *args,
    ]
    return subprocess.run(cmd, capture_output=capture, text=True, cwd=dir, env=os.environ)

def check_cmd_succeeds(dir: Path, args: Iterable[str]) -> None:
    require_successful(run(dir, args, capture=False))

def check_cmd_fails(dir: Path, args: Iterable[str]) -> None:
    require_fail(run(dir, args, capture=False))
