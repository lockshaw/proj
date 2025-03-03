import subprocess
import logging
import shlex
from subprocess import (
    DEVNULL as DEVNULL,
    CalledProcessError as CalledProcessError,
    PIPE,
    CompletedProcess as CompletedProcess,
)
import sys
import io
from typing import (
    overload, 
    Literal, 
    Sequence,
    Tuple,
    Union,
    IO,
    Optional,
    Any,
    Mapping,
)
from pathlib import Path


_l = logging.getLogger(__name__)

def check_call(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(command, **kwargs)


def check_output(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        return subprocess.check_output(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        return subprocess.check_output(command, **kwargs)

@overload
def tee_output(
    command: Union[str, Sequence[str]], 
    *,
    stdout: Optional[IO[bytes]] = None, 
    stderr: Optional[IO[bytes]] = None,
    text: Literal[False] = False, 
    shell: bool = False,
) -> Tuple[bytes, bytes]:
    ...

@overload
def tee_output(
    command: Union[str, Sequence[str]], 
    *,
    stdout: Optional[IO[str]] = None, 
    stderr: Optional[IO[str]] = None, 
    text: Literal[True], 
    shell: bool
) -> Tuple[str, str]:
    ...

def tee_output(command: Union[str, Sequence[str]], *, stdout: Optional[Union[IO[bytes], IO[str]]]=None, stderr: Optional[Union[IO[bytes], IO[str]]]=None, text: bool=False, shell: bool = False) -> Union[Tuple[bytes, bytes], Tuple[str, str]]:
    if isinstance(command, str):
        _l.info(f"+++ $ {command}")
    else:
        if shell:
            command = " ".join(command)
            _l.info(f"+++ $ {command}")
        else:
            pretty_cmd = shlex.join(command)
            _l.info(f"+++ $ {pretty_cmd}")

    proc = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, bufsize=0, text=text, shell=shell)
    stderrs: Any
    stdouts: Any
    if text:
        if stdout is None:
            stdout = sys.stdout
        if stderr is None:
            stderr = sys.stderr
        stderrs = (io.StringIO(), stderr)
        stdouts = (io.StringIO(), stdout)
    else:
        if stdout is None:
            stdout = sys.stdout.buffer
        if stderr is None:
            stderr = sys.stderr.buffer
        stderrs = (io.BytesIO(), stderr)
        stdouts = (io.BytesIO(), stdout)

    def write_both(output, contents):
        output[0].write(contents)
        output[1].write(contents)

    returncode = None
    while True:
        returncode = proc.poll()
        if returncode is None:
            assert proc.stderr is not None
            assert proc.stdout is not None
            write_both(stderrs, proc.stderr.read())
            write_both(stdouts, proc.stdout.read())
        else:
            (remaining_stdout, remaining_stderr) = proc.communicate()
            write_both(stderrs, remaining_stderr)
            write_both(stdouts, remaining_stdout)
            break
    stderrs[0].flush()
    stderrs[1].flush()
    stdouts[0].flush()
    stdouts[1].flush()
    if returncode == 0:
        return (stdouts[0].getvalue(), stderrs[0].getvalue())
    else:
        assert returncode > 0
        raise CalledProcessError(
            returncode=returncode,
            cmd=command,
            output=stdouts[0].getvalue(),
            stderr=stderrs[0].getvalue(),
        )


def hook_stdout(command, *, stdout_hook, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")

    assert isinstance(command, str) == kwargs.get('shell', False)

    proc = subprocess.Popen(command, stdout=PIPE, text=True, bufsize=1, **kwargs)

    output = ''

    def process(s: str) -> None:
        nonlocal output
        if len(s) > 0:
            output += s
            stdout_hook(s)

    while True:
        returncode = proc.poll()
        if returncode is None:
            assert proc.stdout is not None
            process(proc.stdout.readline())
        else:
            (remaining_stdout, _) = proc.communicate()
            process(remaining_stdout)
            break
    if returncode == 0:
        return output
    else:
        assert returncode > 0
        raise CalledProcessError(
            returncode=returncode,
            cmd=command,
        )

def run(command: Sequence[str], stdout: Optional[Union[IO[bytes], IO[str], int]]=None, stderr: Optional[Union[IO[bytes], IO[str], int]]=None, text: bool=False, shell: bool = False, env: Optional[Mapping[str, str]] = None, cwd: Optional[Path] = None, check: bool = False) -> CompletedProcess:
    if not shell:
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")
    return subprocess.run(command, stdout=stdout, stderr=stderr, text=text, shell=shell, env=env, cwd=cwd, check=check)
