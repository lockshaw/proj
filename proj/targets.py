import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Tuple,
    Optional,
    Union,
    Container,
    Set,
    Iterable,
    Iterator,
)
from enum import (
    Enum,
    auto,
)
import re

@dataclass(frozen=True, order=True)
class ConfiguredNames:
    bin_names: Container[str]
    lib_names: Container[str]

class BuildTargetType(Enum):
    LIB = auto()
    BIN = auto()
    TESTS = auto()
    BENCHMARKS = auto()

@dataclass(frozen=True, order=True)
class BuildTarget:
    name: str
    type_: BuildTargetType
    artifact_path: Path

    @staticmethod
    def from_cmake_name(names: ConfiguredNames, cmake_name: str) -> 'BuildTarget':
        result = BuildTarget.try_from_cmake_name(names, cmake_name)
        if result is None:
            raise ValueError(f'Failed to parse {cmake_name=}')
        else:
            return result

    @staticmethod
    def try_from_cmake_name(names: ConfiguredNames, s: str) -> Optional['BuildTarget']:
        if s in names.bin_names:
            return GenericBinTarget(s).build_target
        elif s in names.lib_names:
            return LibTarget(s).build_target
        elif s.endswith('-tests'):
            lib_name = s[:-len('-tests')]
            assert lib_name in names.lib_names
            return LibTarget(lib_name).generic_test_target.build_target
        elif s.endswith('-benchmarks'):
            lib_name = s[:-len('-benchmarks')]
            assert lib_name in names.lib_names
            return LibTarget(lib_name).benchmark_target.build_target
        else:
            return None

    @staticmethod
    def from_str(names: ConfiguredNames, s: str) -> 'BuildTarget':
        result = BuildTarget.try_from_str(names, s)
        if result is None:
            raise ValueError(f'Failed to parse {s=}')
        else:
            return result

    @staticmethod
    def try_from_str(names: ConfiguredNames, s: str) -> Optional['BuildTarget']:
        pieces = s.split(':')
        if s in names.bin_names:
            return GenericBinTarget(pieces[0]).build_target
        elif s in names.lib_names:
            return LibTarget(pieces[0]).build_target
        elif len(pieces) == 2 and is_nonempty_prefix_of(pieces[1], 'benchmarks'):
            lib_name = pieces[0]
            assert lib_name in names.lib_names
            return LibTarget(lib_name).benchmark_target.build_target
        elif len(pieces) == 2 and is_nonempty_prefix_of(pieces[1], 'tests'):
            lib_name = pieces[0]
            assert lib_name in names.lib_names
            return LibTarget(lib_name).generic_test_target.build_target
        else:
            return None

class RunTargetType(Enum):
    BIN = auto()
    TESTS = auto()
    BENCHMARKS = auto()

    @property
    def build_target_type(self) -> BuildTargetType:
        return {
            RunTargetType.BIN: BuildTargetType.BIN,
            RunTargetType.TESTS: BuildTargetType.TESTS,
            RunTargetType.BENCHMARKS: BuildTargetType.BENCHMARKS,
        }[self]

def is_nonempty_prefix_of(needle: str, haystack: str) -> bool:
    return len(needle) > 0 and haystack.startswith(needle)

@dataclass(frozen=True, order=True)
class GenericRunTarget:
    name: str
    type_: RunTargetType
    executable_path: Path
    args: Tuple[str, ...]

    @property
    def build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.name,
            type_=self.type_.build_target_type,
            artifact_path=self.executable_path,
        )


@dataclass(frozen=True, order=True)
class CpuRunTarget:
    generic_run_target: GenericRunTarget

    @property
    def name(self) -> str:
        return self.generic_run_target.name

    @property
    def type_(self) -> RunTargetType:
        return self.generic_run_target.type_

    @property
    def executable_path(self) -> Path:
        return self.generic_run_target.executable_path

    @property
    def args(self) -> Tuple[str, ...]:
        return self.generic_run_target.args

    @property
    def build_target(self) -> BuildTarget:
        return self.generic_run_target.build_target

@dataclass(frozen=True, order=True)
class CudaRunTarget:
    generic_run_target: GenericRunTarget

    @property
    def name(self) -> str:
        return self.generic_run_target.name

    @property
    def type_(self) -> RunTargetType:
        return self.generic_run_target.type_

    @property
    def executable_path(self) -> Path:
        return self.generic_run_target.executable_path

    @property
    def args(self) -> Tuple[str, ...]:
        return self.generic_run_target.args

    @property
    def build_target(self) -> BuildTarget:
        return self.generic_run_target.build_target

def parse_generic_run_target(s: str) -> Union['GenericBinTarget', 'BenchmarkSuiteTarget', 'BenchmarkCaseTarget', 'GenericTestSuiteTarget', 'GenericTestCaseTarget']:
    pieces = s.split(':')
    if len(pieces) == 1:
        return GenericBinTarget(pieces[0])
    elif len(pieces) == 2 and is_nonempty_prefix_of(pieces[1], 'benchmarks'):
        return LibTarget(pieces[0]).benchmark_target
    elif len(pieces) == 3 and is_nonempty_prefix_of(pieces[1], 'benchmarks'):
        return LibTarget(pieces[0]).benchmark_target.get_benchmark_case(pieces[2])
    elif len(pieces) == 2 and is_nonempty_prefix_of(pieces[1], 'tests'):
        return LibTarget(pieces[0]).generic_test_target
    elif len(pieces) == 3 and is_nonempty_prefix_of(pieces[1], 'tests'):
        return LibTarget(pieces[0]).generic_test_target.get_test_case(pieces[2])
    else:
        raise ValueError(f'Failed to parse {s=}')

@dataclass(frozen=True, order=True)
class GenericBinTarget:
    bin_name: str

    @property
    def full_bin_name(self) -> str:
        return self.bin_name

    @property
    def bin_path(self) -> Path:
        return Path('bin') / self.bin_name / self.full_bin_name

    @property
    def build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.full_bin_name,
            type_=BuildTargetType.BIN,
            artifact_path=self.bin_path,
        )

    @property
    def run_target(self) -> GenericRunTarget:
        return GenericRunTarget(
            name=self.full_bin_name,
            type_=RunTargetType.BIN,
            executable_path=self.bin_path,
            args=tuple(),
        )

@dataclass(frozen=True, order=True)
class CpuBinTarget:
    generic_bin_target: GenericBinTarget

    @property
    def full_bin_name(self) -> str:
        return self.generic_bin_target.bin_name

    @property
    def bin_path(self) -> Path:
        return self.generic_bin_target.bin_path

    @property
    def build_target(self) -> BuildTarget:
        return self.generic_bin_target.build_target

    @property
    def run_target(self) -> CpuRunTarget:
        return CpuRunTarget(self.generic_bin_target.run_target)

@dataclass(frozen=True, order=True)
class CudaBinTarget:
    generic_bin_target: GenericBinTarget

    @property
    def full_bin_name(self) -> str:
        return self.generic_bin_target.bin_name

    @property
    def bin_path(self) -> Path:
        return self.generic_bin_target.bin_path

    @property
    def build_target(self) -> BuildTarget:
        return self.generic_bin_target.build_target

    @property
    def run_target(self) -> CudaRunTarget:
        return CudaRunTarget(self.generic_bin_target.run_target)

@dataclass(frozen=True, order=True)
class GenericTestSuiteTarget:
    lib_name: str

    @property
    def lib(self) -> 'LibTarget':
        return LibTarget(self.lib_name)

    @property
    def test_binary_name(self) -> str:
        return self.lib_name + '-tests'

    @property
    def build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.test_binary_name,
            type_=BuildTargetType.TESTS,
            artifact_path=Path('lib') / self.lib_name / 'test' / self.test_binary_name,
        )

    @property
    def run_target(self) -> GenericRunTarget:
        return GenericRunTarget(
            name=self.test_binary_name, 
            type_=RunTargetType.TESTS,
            executable_path=Path('lib') / self.lib_name / 'test' / self.test_binary_name,
            args=('-ts', self.lib_name + '-tests'),
        )

    @property
    def cuda_test_suite(self) -> 'CudaTestSuiteTarget':
        return CudaTestSuiteTarget(self.lib_name)

    @property
    def cpu_test_suite(self) -> 'CpuTestSuiteTarget':
        return CpuTestSuiteTarget(self.lib_name)
    
    def get_test_case(self, test_case_name: str) -> 'GenericTestCaseTarget':
        return GenericTestCaseTarget(
            test_suite=self,
            test_case_name=test_case_name,
        )

@dataclass(frozen=True, order=True)
class CpuTestSuiteTarget:
    lib_name: str

    @property
    def test_binary_name(self) -> str:
        return self.lib_name + '-tests'

    @property
    def build_target(self) -> BuildTarget:
        return self.run_target.build_target

    @property
    def generic_test_suite_target(self) -> GenericTestSuiteTarget:
        return GenericTestSuiteTarget(self.lib_name)

    @property
    def run_target(self) -> CpuRunTarget:
        return CpuRunTarget(
            GenericRunTarget(
                name=self.test_binary_name, 
                type_=RunTargetType.TESTS,
                executable_path=Path('lib') / self.lib_name / 'test' / self.test_binary_name,
                args=('-ts', self.lib_name + '-tests'),
            ),
        )

    def get_test_case(self, test_case_name: str) -> 'CpuTestCaseTarget':
        return CpuTestCaseTarget(
            test_suite=self,
            test_case_name=test_case_name,
        )

@dataclass(frozen=True, order=True)
class CudaTestSuiteTarget:
    lib_name: str

    @property
    def test_binary_name(self) -> str:
        return self.lib_name + '-tests'

    @property
    def build_target(self) -> BuildTarget:
        return self.run_target.build_target

    @property
    def generic_test_suite_target(self) -> GenericTestSuiteTarget:
        return GenericTestSuiteTarget(self.lib_name)

    @property
    def run_target(self) -> CudaRunTarget:
        return CudaRunTarget(
            GenericRunTarget(
                name=self.test_binary_name, 
                type_=RunTargetType.TESTS,
                executable_path=Path('lib') / self.lib_name / 'test' / self.test_binary_name,
                args=('-ts', 'cuda-' + self.lib_name + '-tests'),
            ),
        )

    def get_test_case(self, test_case_name: str) -> 'CudaTestCaseTarget':
        return CudaTestCaseTarget(
            test_suite=self,
            test_case_name=test_case_name,
        )

@dataclass(frozen=True, order=True)
class MixedTestSuiteTarget:
    lib_name: str

    @property
    def test_binary_name(self) -> str:
        return self.lib_name + '-tests'

    @property
    def build_target(self) -> BuildTarget:
        return self.run_target.build_target

    @property
    def run_target(self) -> CudaRunTarget:
        return CudaRunTarget(
            GenericRunTarget(
                name=self.test_binary_name,
                type_=RunTargetType.TESTS,
                executable_path=Path('lib') / self.lib_name / 'test' / self.test_binary_name,
                args=tuple(),
            ),
        )

    def get_test_case(self, test_case_name: str) -> 'GenericTestCaseTarget':
        return GenericTestCaseTarget(
            test_suite=GenericTestSuiteTarget(self.lib_name),
            test_case_name=test_case_name,
        )


@dataclass(frozen=True, order=True)
class GenericTestCaseTarget:
    test_suite: GenericTestSuiteTarget
    test_case_name: str

    @property
    def cpu_test_case(self) -> 'CpuTestCaseTarget':
        return CpuTestCaseTarget(
            test_suite=self.test_suite.cpu_test_suite,
            test_case_name=self.test_case_name,
        )

    @property
    def cuda_test_case(self) -> 'CudaTestCaseTarget':
        return CudaTestCaseTarget(
            test_suite=self.test_suite.cuda_test_suite,
            test_case_name=self.test_case_name,
        )

    @property
    def build_target(self) -> BuildTarget:
        return self.test_suite.build_target

    @property
    def run_target(self) -> GenericRunTarget:
        generic_run_target = self.test_suite.run_target
        return dataclasses.replace(generic_run_target, 
            args=tuple(['--test-case=test_case_name']),
        )

    
@dataclass(frozen=True, order=True)
class CpuTestCaseTarget:
    test_suite: CpuTestSuiteTarget
    test_case_name: str

    @property
    def build_target(self) -> BuildTarget:
        return self.test_suite.build_target
    
    @property
    def run_target(self) -> CpuRunTarget:
        generic_run_target = self.test_suite.run_target.generic_run_target
        return CpuRunTarget(
            dataclasses.replace(generic_run_target, 
                args=tuple(['--test-case=test_case_name']),
            ),
        )

@dataclass(frozen=True, order=True)
class CudaTestCaseTarget:
    test_suite: CudaTestSuiteTarget
    test_case_name: str

    @property
    def build_target(self) -> BuildTarget:
        return self.test_suite.build_target
    
    @property
    def run_target(self) -> CudaRunTarget:
        generic_run_target = self.test_suite.run_target.generic_run_target
        return CudaRunTarget(
            dataclasses.replace(generic_run_target, 
                args=tuple(['--test-case=test_case_name']),
            ),
        )

def parse_generic_test_target(s: str) -> Union[GenericTestSuiteTarget, GenericTestCaseTarget]:
    pieces = s.split(':')
    if len(pieces) == 1:
        return LibTarget(pieces[0]).generic_test_target
    elif len(pieces) == 2:
        return LibTarget(pieces[0]).generic_test_target.get_test_case(pieces[1])
    else:
        raise ValueError(f'Failed to parse {s=}')

def remove_redundant_test_targets(
    targets: Iterable[Union[CpuTestSuiteTarget, CpuTestCaseTarget]]
) -> Iterator[Union[CpuTestSuiteTarget, CpuTestCaseTarget]]:
    all_targets = list(targets)

    suites = {t for t in all_targets if isinstance(t, CpuTestSuiteTarget)}

    seen: Set[Union[CpuTestSuiteTarget, CpuTestCaseTarget]] = set()
    for t in all_targets:
        if t in seen: 
            continue

        if isinstance(t, CpuTestCaseTarget) and t.test_suite in suites:
            continue

        yield t
        seen.add(t)

@dataclass(frozen=True, order=True)
class BenchmarkSuiteTarget:
    lib_name: str

    @property
    def benchmark_binary_name(self) -> str:
        return self.lib_name + '-benchmarks'

    @property
    def build_target(self) -> BuildTarget:
        return self.run_target.build_target

    @property
    def run_target(self) -> CpuRunTarget:
        return CpuRunTarget(
            GenericRunTarget(
                name=self.benchmark_binary_name, 
                type_=RunTargetType.BENCHMARKS,
                executable_path=Path('lib') / self.lib_name / 'benchmark' / self.benchmark_binary_name,
                args=tuple(),
            ),
        )

    def get_benchmark_case(self, case_name: str) -> 'BenchmarkCaseTarget':
        return BenchmarkCaseTarget(
            benchmark_suite=self,
            case_name=case_name,
        )

@dataclass(frozen=True, order=True)
class BenchmarkCaseTarget:
    benchmark_suite: BenchmarkSuiteTarget
    case_name: str

    @property
    def build_target(self) -> BuildTarget:
        return self.benchmark_suite.build_target

    @property
    def run_target(self) -> CpuRunTarget:
        generic_run_target = self.benchmark_suite.run_target.generic_run_target
        return CpuRunTarget(
            dataclasses.replace(generic_run_target, 
                args=tuple([f'--benchmark_filter=^{re.escape(self.case_name)}$']),
            ),
        )

def parse_generic_benchmark_target(s: str) -> Union[BenchmarkSuiteTarget, BenchmarkCaseTarget]:
    pieces = s.split(':')
    if len(pieces) == 1:
        return LibTarget(pieces[0]).benchmark_target
    elif len(pieces) == 2:
        return LibTarget(pieces[0]).benchmark_target.get_benchmark_case(pieces[1])
    else:
        raise ValueError(f'Failed to parse {s=}')

@dataclass(frozen=True, order=True)
class LibTarget:
    lib_name: str

    @property
    def full_lib_name(self) -> str:
        return self.lib_name

    @property
    def generic_test_target(self) -> GenericTestSuiteTarget:
        return GenericTestSuiteTarget(self.lib_name)

    @property
    def mixed_test_target(self) -> MixedTestSuiteTarget:
        return MixedTestSuiteTarget(self.lib_name)

    @property
    def cpu_test_target(self) -> CpuTestSuiteTarget:
        return CpuTestSuiteTarget(self.lib_name)

    @property
    def cuda_test_target(self) -> CudaTestSuiteTarget:
        return CudaTestSuiteTarget(self.lib_name)

    @property
    def benchmark_target(self) -> BenchmarkSuiteTarget:
        return BenchmarkSuiteTarget(self.lib_name)

    @property
    def so_path(self) -> Path:
        return Path('lib') / self.lib_name / f'lib{self.full_lib_name}.so'

    @property
    def build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.full_lib_name,
            type_=BuildTargetType.LIB,
            artifact_path=self.so_path,
        )

    @property
    def all_build_targets(self) -> Tuple[BuildTarget, ...]:
        return (
            self.build_target,
            self.generic_test_target.build_target,
            self.benchmark_target.build_target,
        )

    @staticmethod
    def from_str(s: str) -> 'LibTarget':
        return LibTarget(s)
