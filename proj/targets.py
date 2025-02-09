from dataclasses import dataclass
from pathlib import Path
from .config_file import ProjectConfig
from typing import (
    Union,
)
from enum import (
    Enum,
    auto,
)

class BuildTargetType(Enum):
    BIN = auto()
    LIB = auto()
    TESTS = auto()
    BENCHMARKS = auto()

@dataclass(frozen=True, order=True)
class BuildTarget:
    name: str
    type_: BuildTargetType

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

    @property
    def build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.name,
            type_=self.type_.build_target_type,
        )

@dataclass(frozen=True, order=True)
class BinTarget:
    bin_name: str

    @property
    def bin_path(self) -> Path:
        return Path('bin') / self.bin_name / self.bin_name

    @property
    def bin_build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.bin_name,
            type_=BuildTargetType.BIN,
        )

    @property
    def bin_run_target(self) -> RunTarget:
        return RunTarget(
            name=self.bin_name,
            type_=RunTargetType.BIN,
            executable_path=self.bin_path,
        )

@dataclass(frozen=True, order=True)
class LibTarget:
    lib_name: str

    @property
    def test_name(self) -> str:
        return self.lib_name + '-tests'

    @property
    def benchmark_name(self) -> str:
        return self.lib_name + '-benchmarks'

    @property
    def benchmark_path(self) -> Path:
        return Path('lib') / self.lib_name / 'benchmark' / self.benchmark_name

    @property
    def tests_path(self) -> Path:
        return Path('lib') / self.lib_name / 'test' / self.test_name
    
    @property
    def lib_build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.lib_name,
            type_=BuildTargetType.LIB,
        )

    @property
    def benchmark_build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.benchmark_name,
            type_=BuildTargetType.BENCHMARKS,
        )

    @property
    def benchmark_run_target(self) -> RunTarget:
        return RunTarget(
            name=self.benchmark_name,
            type_=RunTargetType.BENCHMARKS,
            executable_path=self.benchmark_path,
        )

    @property
    def tests_build_target(self) -> BuildTarget:
        return BuildTarget(
            name=self.test_name,
            type_=BuildTargetType.TESTS,
        )

    @property
    def tests_run_target(self) -> RunTarget:
        return RunTarget(
            name=self.test_name,
            type_=RunTargetType.TESTS,
            executable_path=self.tests_path,
        )

def parse_target(config: ProjectConfig, name: str) -> Union[BinTarget, LibTarget]:
    if name in config.bin_targets:
        return BinTarget(name)
    else:
        assert name in config.lib_targets
        return LibTarget(name)
