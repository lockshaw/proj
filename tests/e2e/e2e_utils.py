from pathlib import Path
import subprocess
from typing import (
    Iterable,
    Mapping,
    Optional,
)
import os
import sys

def require_successful(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    if r.returncode != 0:
        print('Invocation stderr:', file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        print('Invocation stdout:', file=sys.stdout)
        print(r.stdout, file=sys.stdout)
    assert r.returncode == 0
    return r

def require_fail(r: subprocess.CompletedProcess) -> subprocess.CompletedProcess:
    assert r.returncode != 0
    return r

def run(dir: Path, args: Iterable[str], capture: bool = True, env: Optional[Mapping[str, str]] = None, verbose: bool = True) -> subprocess.CompletedProcess:
    _env = env if env is not None else {}

    _args = list(args)
    cmd = ['proj', _args[0]]
    if verbose:
        cmd.append('-vv')
    cmd = [*cmd, *_args[1:]]
    print(f'Running {cmd=}')
    return subprocess.run(cmd, capture_output=capture, text=True, cwd=dir, env={**os.environ, **_env})

def check_cmd_succeeds(dir: Path, args: Iterable[str], env: Optional[Mapping[str, str]] = None) -> None:
    require_successful(run(dir, args, capture=False, env=env))

def check_cmd_fails(dir: Path, args: Iterable[str], env: Optional[Mapping[str, str]] = None) -> None:
    require_fail(run(dir, args, capture=False, env=env))
