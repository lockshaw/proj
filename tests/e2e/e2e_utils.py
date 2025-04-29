from pathlib import Path
import subprocess
from typing import (
    Iterable,
    Mapping,
)
import os
import immutables as imm

def require_successful(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    assert r.returncode == 0, r.stderr
    return r

def require_fail(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    assert r.returncode != 0
    return r

def run(dir: Path, args: Iterable[str], capture: bool = True, env: Mapping[str, str] = imm.Map(), verbose: bool = True) -> subprocess.CompletedProcess:
    _args = list(args)
    cmd = ['proj', _args[0]]
    if verbose:
        cmd.append('-v')
    cmd = [*cmd, *_args[1:]]
    print(f'Running {cmd=}')
    return subprocess.run(cmd, capture_output=capture, text=True, cwd=dir, env={**os.environ, **env})

def check_cmd_succeeds(dir: Path, args: Iterable[str], env: Mapping[str, str] = imm.Map()) -> None:
    require_successful(run(dir, args, capture=False, env=env))

def check_cmd_fails(dir: Path, args: Iterable[str], env: Mapping[str, str] = imm.Map()) -> None:
    require_fail(run(dir, args, capture=False, env=env))
