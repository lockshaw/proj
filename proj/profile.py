from typing import (
    Union,
)
from .targets import (
    CpuRunTarget,
    CudaRunTarget,
)
from . import subprocess_trace as subprocess
from pathlib import Path
from enum import StrEnum
import logging

_l = logging.getLogger(__name__)

class ProfilingTool(StrEnum):
    PERF = 'perf'
    CALLGRIND = 'callgrind'

def output_file_for_target(target: Union[CpuRunTarget, CudaRunTarget], tool: ProfilingTool) -> Path:
    return target.executable_path.parent / (target.executable_path.name + '.' + tool)

def profile_target(build_dir: Path, target: Union[CpuRunTarget, CudaRunTarget], dry_run: bool, tool: ProfilingTool) -> Path:
    output_file = build_dir / output_file_for_target(target, tool)

    if tool == ProfilingTool.PERF:
        profile_target_with_perf(build_dir, target, output_file, dry_run)
    else:
        assert tool == ProfilingTool.CALLGRIND
        profile_target_with_callgrind(build_dir, target, output_file)

    return output_file

def profile_target_with_perf(build_dir: Path, target: Union[CpuRunTarget, CudaRunTarget], output_file: Path, dry_run: bool) -> None:
    extra_flags = []
    if dry_run:
        extra_flags.append('--dry-run')

    cmd = [
        'perf', 
        'record',
        '--call-graph=dwarf', 
        '-F',
        '100',
        *extra_flags,
        '--output',
        str(output_file),
        '--',
        str(build_dir / target.executable_path),
        *target.args,
    ]

    subprocess.check_call(cmd)

    if not dry_run:
        assert output_file.is_file()

def profile_target_with_callgrind(build_dir: Path, target: Union[CpuRunTarget, CudaRunTarget], output_file: Path) -> None:
    cmd = [
        'valgrind', 
        '--tool=callgrind',
        f'--callgrind-out-file={output_file}',
        str(build_dir / target.executable_path),
        *target.args,
    ]

    subprocess.check_call(cmd)

    assert output_file.is_file()


def visualize_profile(profile_path: Path, tool: ProfilingTool) -> None:
    if tool == ProfilingTool.PERF:
        visualize_profile_with_hotspot(profile_path)
    else:
        assert tool == ProfilingTool.CALLGRIND
        visualize_profile_with_kcachegrind(profile_path)

def visualize_profile_with_hotspot(profile_path: Path) -> None:
    assert profile_path.is_file()

    subprocess.check_call([
        'hotspot',
        str(profile_path),
    ])

def visualize_profile_with_kcachegrind(profile_path: Path) -> None:
    assert profile_path.is_file()

    subprocess.check_call([
        'kcachegrind',
        str(profile_path),
    ])
