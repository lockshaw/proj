from pathlib import Path
import subprocess
from typing import Union
import os

def require_successful(r: Union[subprocess.CompletedProcess, subprocess.CalledProcessError]) -> subprocess.CompletedProcess:
    assert isinstance(r, subprocess.CompletedProcess)
    assert r.returncode == 0
    return r

def require_fail(r: Union[subprocess.CompletedProcess, subprocess.CalledProcessError]) -> subprocess.CalledProcessError:
    assert isinstance(r, subprocess.CalledProcessError)
    return r

def run(dir: Path, args, capture: bool = True) -> Union[subprocess.CompletedProcess, subprocess.CalledProcessError]:
    cmd = [
        'proj',
        *args,
    ]
    try:
        return subprocess.run(cmd, capture_output=capture, text=True, cwd=dir, env=os.environ)
    except subprocess.CalledProcessError as e:
        return e

def check_cmd_succeeds(dir: Path, args) -> None:
    require_successful(run(dir, args, capture=False))
