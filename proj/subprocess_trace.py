import subprocess
import logging
import shlex
from subprocess import (
    DEVNULL as DEVNULL,
    CalledProcessError as CalledProcessError,
    PIPE,
    CompletedProcess as CompletedProcess,
    TimeoutExpired as TimeoutExpired,
)
import sys
import io
from typing import (
    Sequence,
    Tuple,
    Union,
    IO,
    Optional,
    Any,
    Mapping,
)
from pathlib import Path
import os
import time

_l = logging.getLogger(__name__)


def check_call(command, **kwargs):
    cwd_str = kwargs.get('cwd', '')

    if kwargs.get("shell", False):
        assert isinstance(command, str)
        _l.debug(f"+++ {cwd_str}$ {command}")
        subprocess.check_call(command, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.debug(f"+++ {cwd_str}$ {pretty_cmd}")
        subprocess.check_call(command, **kwargs)


def check_output(command, **kwargs):
    cwd_str = kwargs.get('cwd', '')

    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.debug(f"+++ {cwd_str}$ {pretty_cmd}")
        return subprocess.check_output(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.debug(f"+++ {cwd_str}$ {pretty_cmd}")
        return subprocess.check_output(command, **kwargs)


def tee_output(
    command: Union[str, Sequence[str]],
    *,
    stdout: Optional[IO[bytes]] = None,
    stderr: Optional[IO[bytes]] = None,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
    shell: bool = False,
    check: bool = True,
) -> Tuple[bytes, bytes]:
    cwd_str = str(cwd) if cwd is not None else ''

    if isinstance(command, str):
        _l.debug(f"+++ {cwd_str}$ {command}")
    else:
        if shell:
            command = shlex.join(command)
            _l.debug(f"+++ {cwd_str}$ {command}")
        else:
            pretty_cmd = shlex.join(command)
            _l.debug(f"+++ {cwd_str}$ {pretty_cmd}")

    proc = subprocess.Popen(
        command, stdout=PIPE, stderr=PIPE, bufsize=0, text=False, shell=shell, env=env, cwd=cwd,
    )
    stderrs: Any
    stdouts: Any

    if stdout is None:
        stdout = sys.stdout.buffer
    if stderr is None:
        stderr = sys.stderr.buffer
    stderrs = (io.BytesIO(), stderr)
    stdouts = (io.BytesIO(), stdout)

    def write_both(output, contents):
        if contents is not None:
            output[0].write(contents)
            output[1].write(contents)

    assert proc.stdout is not None
    assert proc.stderr is not None
    assert not proc.stdout.closed
    assert not proc.stderr.closed

    os.set_blocking(proc.stderr.fileno(), False)
    os.set_blocking(proc.stdout.fileno(), False)

    returncode = None
    current_time = time.time()
    while True:
        last_time = time.time()
        _l.debug('Polling...')
        returncode = proc.poll()
        _l.debug('Polling returned with returncode %s', returncode)
        if returncode is None:
            _l.debug('Reading from stdout')
            stdout_contents = proc.stdout.read()
            stdout_contents_len = None if stdout_contents is None else len(stdout_contents)
            _l.debug('Read %s characters from process stdout', stdout_contents_len)
            _l.debug('Reading from stderr')
            stderr_contents = proc.stderr.read()
            stderr_contents_len = None if stderr_contents is None else len(stderr_contents)
            _l.debug('Read %s characters from process stderr', stderr_contents_len)
            write_both(stdouts, stdout_contents)
            write_both(stderrs, stderr_contents)
        else:
            _l.debug('Reading remaining output from command')
            (remaining_stdout, remaining_stderr) = proc.communicate()
            write_both(stderrs, remaining_stderr)
            write_both(stdouts, remaining_stdout)
            break
        last_time = current_time
        current_time = time.time()
        time_delta = current_time - last_time
        time.sleep(max(0.05 - time_delta, 0.0))
    stderrs[0].flush()
    stderrs[1].flush()
    stdouts[0].flush()
    stdouts[1].flush()

    out = stdouts[0].getvalue()
    err = stderrs[0].getvalue()

    if returncode == 0 or not check:
        return (
            out,
            err,
        )
    else:
        assert returncode > 0
        raise CalledProcessError(
            returncode=returncode,
            cmd=command,
            output=out,
            stderr=err,
        )


def hook_stdout(command, *, stdout_hook, **kwargs):
    cwd_str = kwargs.get('cwd')

    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
    else:
        pretty_cmd = shlex.join(command)
    _l.debug("+++ %s$ %s", cwd_str, pretty_cmd)

    assert isinstance(command, str) == kwargs.get("shell", False)

    proc = subprocess.Popen(command, stdout=PIPE, text=True, bufsize=1, **kwargs)

    output = ""

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


def run(
    command: Sequence[str],
    stdout: Optional[Union[IO[bytes], IO[str], int]] = None,
    stderr: Optional[Union[IO[bytes], IO[str], int]] = None,
    text: bool = False,
    shell: bool = False,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Path] = None,
    check: bool = False,
    timeout: Optional[float] = None,
) -> CompletedProcess:
    cwd_str = str(cwd) if cwd is not None else ''

    if not shell:
        pretty_cmd = " ".join(command)
        _l.debug(f"+++ {cwd_str}$ {pretty_cmd}")
    else:
        pretty_cmd = shlex.join(command)
        _l.debug(f"+++ {cwd_str}$ {pretty_cmd}")
    return subprocess.run(
        command,
        stdout=stdout,
        stderr=stderr,
        text=text,
        shell=shell,
        env=env,
        cwd=cwd,
        check=check,
        timeout=timeout,
    )
