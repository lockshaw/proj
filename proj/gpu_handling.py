from . import subprocess_trace as subprocess
import logging
from typing import (
    Sequence,
    Callable,
    TypeVar,
    Generic,
    Protocol,
    Tuple,
)
from dataclasses import dataclass
from .targets import (
    BuildTarget,
    RunTarget,
)

_l = logging.getLogger(__name__)

def check_if_machine_supports_gpu() -> bool:
    try:
        subprocess.check_call(['nvidia-smi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        _l.info('Could not find executable nvidia-smi in path')
        return False
    except subprocess.CalledProcessError:
        _l.info('nvidia-smi returned nonzero error code')
        return False

class BuildableRunnable(Protocol):
    @property
    def build_target(self) -> BuildTarget:
        ...

    @property
    def run_target(self) -> RunTarget:
        ...

BR = TypeVar('BR', bound=BuildableRunnable)

@dataclass(frozen=True)
class BuildRunPlan(Generic[BR]):
    targets_to_build: Sequence[BR]
    targets_to_run: Sequence[BR]
    failed_gpu_check: bool

    @property
    def build_targets(self) -> Tuple[BuildTarget, ...]:
        return tuple(t.build_target for t in self.targets_to_build)

    @property
    def run_targets(self) -> Tuple[RunTarget, ...]:
        return tuple(t.run_target for t in self.targets_to_run)

def infer_build_run_plan(
    requested_targets: Sequence[BR],
    target_requires_gpu: Callable[[BR], bool],
    skip_run_gpu_targets: bool,
    skip_build_gpu_targets: bool,
    skip_run_cpu_targets: bool,
    skip_build_cpu_targets: bool,
) -> BuildRunPlan[BR]:
    def not_target_requires_gpu(target: BR) -> bool:
        return not target_requires_gpu(target)

    gpu_targets_to_build = list(filter(target_requires_gpu, requested_targets))
    if skip_build_gpu_targets:
        _l.info('Skipping build of gpu targets: %s', gpu_targets_to_build)
        gpu_targets_to_build = []

    cpu_targets_to_build = list(filter(not_target_requires_gpu, requested_targets))
    if skip_build_cpu_targets:
        _l.info('Skipping build of cpu targets: %s', cpu_targets_to_build)
        cpu_targets_to_build = []

    targets_to_build = cpu_targets_to_build + gpu_targets_to_build

    if skip_run_cpu_targets and len(cpu_targets_to_build) > 0:
        _l.info('Skipping running cpu targets: %s', cpu_targets_to_build)
        cpu_targets_to_run = []
    else:
        cpu_targets_to_run = cpu_targets_to_build

    if skip_run_gpu_targets and len(gpu_targets_to_build) > 0:
        _l.info('Skipping running gpu targets: %s', gpu_targets_to_build)
        gpu_targets_to_run = []
    else:
        gpu_targets_to_run = gpu_targets_to_build

    targets_to_run = cpu_targets_to_run + gpu_targets_to_run

    gpu_available = check_if_machine_supports_gpu()
    failed_gpu_check = (not gpu_available) and len(gpu_targets_to_run) > 0

    return BuildRunPlan(
        targets_to_build=[t for t in targets_to_build],
        targets_to_run=[t for t in targets_to_run],
        failed_gpu_check=failed_gpu_check,
    )
