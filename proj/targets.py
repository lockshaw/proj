import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Tuple,
    Optional,
    Union,
    Container,
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
            return BinTarget(s).build_target
        elif s in names.lib_names:
            return LibTarget(s).build_target
        elif s.endswith('-tests'):
            lib_name = s[:-len('-tests')]
            assert lib_name in names.lib_names
            return LibTarget(lib_name).test_target.build_target
        elif s.endswith('-benchmarks'):
            lib_name = s[:-len('-benchmarks')]
            assert lib_name in names.lib_names
            return LibTarget(lib_name).benchmark_target.build_target
        else:
            return None

    @staticmethod
    def from_str(s: str) -> 'BuildTarget':
        result = BuildTarget.try_from_str(s)
        if result is None:
            raise ValueError(f'Failed to parse {s=}')
        else:
            return result

    @staticmethod
    def try_from_str(s: str) -> Optional['BuildTarget']:
        pieces = s.split(':')
        if len(pieces) == 2 and pieces[0] == 'bin':
            return BinTarget(pieces[1]).build_target
        elif len(pieces) == 2 and pieces[0] == 'lib':
            return LibTarget(pieces[1]).build_target
        elif len(pieces) == 2 and pieces[0] == 'bench':
            return LibTarget(pieces[1]).benchmark_target.build_target
        elif len(pieces) == 2 and pieces[0] == 'test':
            return LibTarget(pieces[1]).test_target.build_target
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

@dataclass(frozen=True, order=True)
class RunTarget:
    name: str
    type_: RunTargetType
    executable_path: Path
    args: Tuple[str, ...]

    @property
    def run_target(self) -> 'RunTarget':
        return self

    @property
    def build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.name,
            type_=self.type_.build_target_type,
            artifact_path=self.executable_path,
        )

    @staticmethod
    def from_str(s: str) -> 'RunTarget':
        pieces = s.split(':')
        if len(pieces) == 1:
            return BinTarget(pieces[0]).run_target
        elif len(pieces) == 2 and pieces[1] == 'benchmarks':
            return LibTarget(pieces[0]).benchmark_target.run_target
        elif len(pieces) == 3 and pieces[1] == 'benchmarks':
            return LibTarget(pieces[0]).benchmark_target.get_benchmark_case(pieces[2]).run_target
        elif len(pieces) == 2 and pieces[1] == 'tests':
            return LibTarget(pieces[0]).test_target.run_target
        elif len(pieces) == 3 and pieces[1] == 'tests':
            return LibTarget(pieces[0]).test_target.get_test_case(pieces[2]).run_target
        else:
            raise ValueError(f'Failed to parse {s=}')

@dataclass(frozen=True, order=True)
class BinTarget:
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
    def run_target(self) -> RunTarget:
        return RunTarget(
            name=self.full_bin_name,
            type_=RunTargetType.BIN,
            executable_path=self.bin_path,
            args=tuple(),
        )

@dataclass(frozen=True, order=True)
class TestSuiteTarget:
    lib_name: str

    @property
    def test_binary_name(self) -> str:
        return self.lib_name + '-tests'

    @property
    def build_target(self) -> BuildTarget:
        return self.run_target.build_target

    @property
    def run_target(self) -> RunTarget:
        return RunTarget(
            name=self.test_binary_name, 
            type_=RunTargetType.TESTS,
            executable_path=Path('lib') / self.lib_name / 'test' / self.test_binary_name,
            args=tuple(),
        )

    def get_test_case(self, test_case_name: str) -> 'TestCaseTarget':
        return TestCaseTarget(
            test_suite=self,
            test_case_name=test_case_name,
        )

@dataclass(frozen=True, order=True)
class TestCaseTarget:
    test_suite: TestSuiteTarget
    test_case_name: str

    @property
    def build_target(self) -> BuildTarget:
        return self.test_suite.build_target
    
    @property
    def run_target(self) -> RunTarget:
        suite_run_target = self.test_suite.run_target
        return dataclasses.replace(suite_run_target, 
            args=tuple(['--test-case=test_case_name']),
        )

def parse_generic_test_target(s: str) -> Union[TestSuiteTarget, TestCaseTarget]:
    pieces = s.split(':')
    if len(pieces) == 1:
        return LibTarget(pieces[0]).test_target
    elif len(pieces) == 2:
        return LibTarget(pieces[0]).test_target.get_test_case(pieces[1])
    else:
        raise ValueError(f'Failed to parse {s=}')

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
    def run_target(self) -> RunTarget:
        return RunTarget(
            name=self.benchmark_binary_name, 
            type_=RunTargetType.BENCHMARKS,
            executable_path=Path('lib') / self.lib_name / 'benchmark' / self.benchmark_binary_name,
            args=tuple(),
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
    def run_target(self) -> RunTarget:
        suite_run_target = self.benchmark_suite.run_target
        return dataclasses.replace(suite_run_target, 
            args=tuple([f'--benchmark_filter=^{re.escape(self.case_name)}$']),
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
    def test_target(self) -> TestSuiteTarget:
        return TestSuiteTarget(self.lib_name)

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
            self.test_target.build_target,
            self.benchmark_target.build_target,
        )

    @staticmethod
    def from_str(s: str) -> 'LibTarget':
        return LibTarget(s)
