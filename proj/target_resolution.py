from .config_file import (
    ProjectConfig,
    resolve_bin_target,
    resolve_test_target,
)
from pathlib import Path
from .targets import (
    GenericBinTarget,
    BenchmarkSuiteTarget,
    BenchmarkCaseTarget,
    GenericTestSuiteTarget,
    GenericTestCaseTarget,
    CpuRunTarget,
    CudaRunTarget,
    CudaBinTarget,
    CpuBinTarget,
    MixedTestSuiteTarget,
    CpuTestSuiteTarget,
    CudaTestSuiteTarget,
    CpuTestCaseTarget,
    CudaTestCaseTarget,
)
from typing import (
    Union,
)
from .gpu_handling import (
    check_if_machine_supports_cuda,
)
from .failure import fail_with_error
from .build import (
    build_targets,
)
from .testing import (
    resolve_test_case_target_using_build,
)


def fully_resolve_run_target(
    config: ProjectConfig,
    build_dir: Path,
    unresolved_target: Union[
        GenericBinTarget,
        BenchmarkSuiteTarget,
        BenchmarkCaseTarget,
        GenericTestSuiteTarget,
        GenericTestCaseTarget,
    ],
    jobs: int,
    verbosity: int,
    skip_gpu: bool,
) -> Union[CpuRunTarget, CudaRunTarget,]:
    resolved_target: Union[
        CpuBinTarget,
        CudaBinTarget,
        BenchmarkSuiteTarget,
        BenchmarkCaseTarget,
        MixedTestSuiteTarget,
        CpuTestSuiteTarget,
        CudaTestSuiteTarget,
        CpuTestCaseTarget,
        CudaTestCaseTarget,
        GenericTestCaseTarget,
    ]
    if isinstance(unresolved_target, GenericBinTarget):
        resolved_target = resolve_bin_target(config, unresolved_target)
    elif isinstance(unresolved_target, (BenchmarkSuiteTarget, BenchmarkCaseTarget)):
        resolved_target = unresolved_target
    else:
        assert isinstance(
            unresolved_target, (GenericTestSuiteTarget, GenericTestCaseTarget)
        )
        resolved_target = resolve_test_target(config, unresolved_target)

    if skip_gpu and isinstance(resolved_target, MixedTestSuiteTarget):
        resolved_target = resolved_target.cpu_test_suite_target

    has_cuda = check_if_machine_supports_cuda()
    if not has_cuda and isinstance(resolved_target, MixedTestSuiteTarget):
        fail_with_error(
            f"Cannot run target {unresolved_target} as no gpus are available on the current machine. "
            "Pass --skip-gpu to skip running tests that require a GPU."
        )
    if not has_cuda and isinstance(
        resolved_target, (CudaBinTarget, CudaTestCaseTarget)
    ):
        fail_with_error(
            f"Cannot run target {unresolved_target} as no gpus are available on the current machine."
        )

    build_targets(
        config=config,
        targets=[resolved_target.build_target],
        dtgen_skip=False,
        jobs=jobs,
        verbosity=verbosity,
        build_dir=build_dir,
    )

    fully_resolved_target: Union[
        CpuBinTarget,
        CudaBinTarget,
        BenchmarkSuiteTarget,
        BenchmarkCaseTarget,
        MixedTestSuiteTarget,
        CpuTestSuiteTarget,
        CudaTestSuiteTarget,
        CpuTestCaseTarget,
        CudaTestCaseTarget,
    ]
    if isinstance(resolved_target, GenericTestCaseTarget):
        fully_resolved_target = resolve_test_case_target_using_build(
            config, resolved_target, build_dir
        )
    else:
        fully_resolved_target = resolved_target

    return fully_resolved_target.run_target
