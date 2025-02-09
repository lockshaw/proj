from .targets import RunTarget
from . import subprocess_trace as subprocess
from pathlib import Path
from typing import (
    Optional,
)

def output_file_for_target(target: RunTarget) -> Path:
    return target.executable_path.parent / (target.executable_path.name + '.perf')

def profile_target(build_dir: Path, target: RunTarget) -> Path:
    output_file = build_dir / output_file_for_target(target)

    subprocess.check_call([
        'perf', 
        'record',
        '--call-graph=dwarf', 
        '-F',
        '100',
        '--output',
        str(output_file),
        '--',
        str(build_dir / target.executable_path)
    ])

    return output_file

def visualize_profile():
    ...
