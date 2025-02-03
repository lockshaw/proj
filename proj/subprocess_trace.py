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
        return subprocess.checkout_output(command, **kwargs)


def tee_output(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")

    proc = subprocess.Popen(command, stdout=PIPE, stderr=PIPE)
    if kwargs.get('text', False):
        stderr = io.TextIO()
        stdout = io.TextIO()
    else:
        stderr = io.BytesIO()
        stdout = io.BytesIO()
    returncode = None
    while True:
        returncode = proc.poll()
        if returncode is None:
            line = proc.stderr.read()
            if line:
                sys.stderr.write(line)
                stderr.write(line)
            line = proc.stdout.readline()
            if line:
                sys.stdout.write(line)
                stdout.write(line)
        else:
            (remaining_stdout, remaining_stderr) = proc.communicate()
            print(remaining_stderr, file=sys.stderr, flush=True)
            print(remaining_stdout, file=sys.stdout, flush=True)
    if returncode == 0:
        return stdout
    else:
        assert returncode > 0
        raise CalledProcessError(
            returncode=returncode,
            cmd=command,
            output=stdout.getvalue(),
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )


def run(command, **kwargs):
    if kwargs.get("shell", False):
        pretty_cmd = " ".join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f"+++ $ {pretty_cmd}")
        subprocess.check_call(command, **kwargs)
