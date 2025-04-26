from proj.subprocess_trace import (
    tee_output_bytes, 
    tee_output_str,
    CalledProcessError,
)
import io

def test_tee_output_to_stdout() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    (stdout2_val, stderr2_val) = tee_output_str(['echo', 'hello world'], stdout=stdout, stderr=stderr)
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    assert stdout1_val == 'hello world\n'
    assert stderr1_val == ''

def test_tee_output_no_trailing_newline() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    (stdout2_val, stderr2_val) = tee_output_str(['echo', '-n', 'hello world'], stdout=stdout, stderr=stderr)
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    assert stdout1_val == 'hello world'
    assert stderr1_val == ''

def test_tee_output_to_stderr() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        (stdout2_val, stderr2_val) = tee_output_str('echo "error world" 1>&2 && echo "okay world"', stdout=stdout, stderr=stderr, shell=True)
    except CalledProcessError as e:
        stdout2_val = e.stdout
        stderr2_val = e.stderr
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    correct_stderr_val = 'error world\n'
    correct_stdout_val = 'okay world\n'

    assert (stderr1_val, stdout1_val) == (correct_stderr_val, correct_stdout_val)

def test_tee_output_bytes_output() -> None:
    stdout = io.BytesIO()
    stderr = io.BytesIO()
    (stdout2_val, stderr2_val) = tee_output_bytes('echo "error world" 1>&2 && echo "okay world"', stdout=stdout, stderr=stderr, shell=True)
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    assert stdout1_val == b'okay world\n'
    assert stderr1_val == b'error world\n'

def test_tee_output_real_stderr_stdout() -> None:
    (stdout_val, stderr_val) = tee_output_bytes('echo "error world" 1>&2 && echo "okay world"', shell=True)

    assert stdout_val == b'okay world\n'
    assert stderr_val == b'error world\n'

def test_tee_output_real_stderr_stdout_command_fails() -> None:
    try:
        tee_output_bytes('echo "error world" 1>&2 && echo "okay world" && false', shell=True)
        assert False
    except CalledProcessError as e:
        stdout_val = e.stdout
        stderr_val = e.stderr
        assert stdout_val == b'okay world\n'
        assert stderr_val == b'error world\n'

def test_tee_output_real_stderr_stdout_command_fails_text_mode() -> None:
    try:
        tee_output_str('echo "error world" 1>&2 && echo "okay world" && false', shell=True)
        assert False
    except CalledProcessError as e:
        stdout_val = e.stdout
        stderr_val = e.stderr
        assert stdout_val == 'okay world\n'
        assert stderr_val == 'error world\n'
