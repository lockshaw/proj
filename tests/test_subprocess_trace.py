from proj.subprocess_trace import (
    tee_output, 
    CalledProcessError,
)
import io

def test_tee_output_to_stdout():
    stdout = io.StringIO()
    stderr = io.StringIO()
    (stdout2_val, stderr2_val) = tee_output(['echo', 'hello world'], stdout=stdout, stderr=stderr, text=True)
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    assert stdout1_val == 'hello world\n'
    assert stderr1_val == ''

def test_tee_output_no_trailing_newline():
    stdout = io.StringIO()
    stderr = io.StringIO()
    (stdout2_val, stderr2_val) = tee_output(['echo', '-n', 'hello world'], stdout=stdout, stderr=stderr, text=True)
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    assert stdout1_val == 'hello world'
    assert stderr1_val == ''

def test_tee_output_to_stderr():
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        (stdout2_val, stderr2_val) = tee_output('echo "error world" 1>&2 && echo "okay world"', stdout=stdout, stderr=stderr, text=True, shell=True)
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

def test_tee_output_bytes_output():
    stdout = io.BytesIO()
    stderr = io.BytesIO()
    (stdout2_val, stderr2_val) = tee_output('echo "error world" 1>&2 && echo "okay world"', stdout=stdout, stderr=stderr, shell=True)
    stdout1_val = stdout.getvalue()
    stderr1_val = stderr.getvalue()

    assert stdout1_val == stdout2_val
    assert stderr1_val == stderr2_val

    assert stdout1_val == b'okay world\n'
    assert stderr1_val == b'error world\n'
