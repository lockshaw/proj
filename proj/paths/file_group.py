from dataclasses import dataclass, field
from .component import Component
from pathlib import PurePath
from .role_in_group import RoleInGroup
from typing import (
    Optional,
)
from .file import File

@dataclass(frozen=True)
class FileGroup:
    group_path: PurePath
    component: Optional[Component] = field(default=None)

    def __str__(self) -> str:
        return f'{self.component}:{self.group_path}'

    @property
    def public_header(self) -> 'File':
        return File(self, RoleInGroup.PUBLIC_HEADER)

    @property
    def source(self) -> 'File':
        return File(self, RoleInGroup.SOURCE)

    @property
    def test(self) -> 'File':
        return File(self, RoleInGroup.TEST)

    @property
    def benchmark_header(self) -> 'File':
        return File(self, RoleInGroup.BENCHMARK_HEADER)

    @property
    def benchmark_source(self) -> 'File':
        return File(self, RoleInGroup.BENCHMARK_SOURCE)

    @property
    def generated_header(self) -> 'File':
        return File(self, RoleInGroup.GENERATED_HEADER)

    @property
    def generated_source(self) -> 'File':
        return File(self, RoleInGroup.GENERATED_SOURCE)

    @property
    def dtgen_toml(self) -> 'File':
        return File(self, RoleInGroup.DTGEN_TOML)
