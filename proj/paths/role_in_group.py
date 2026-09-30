from enum import (
    Enum,
    auto,
)

class RoleInGroup(Enum):
    PUBLIC_HEADER = auto()
    SOURCE = auto()
    TEST = auto()
    BENCHMARK_SOURCE = auto()
    BENCHMARK_HEADER = auto()
    DTGEN_TOML = auto()
    GENERATED_HEADER = auto()
    GENERATED_SOURCE = auto()

    @property
    def shortname(self) -> str:
        return {
            RoleInGroup.PUBLIC_HEADER: 'hdr',
            RoleInGroup.SOURCE: 'src',
            RoleInGroup.TEST: 'tst',
            RoleInGroup.BENCHMARK_SOURCE: 'bmk',
            RoleInGroup.BENCHMARK_HEADER: 'bmkhdr',
            RoleInGroup.DTGEN_TOML: 'toml',
            RoleInGroup.GENERATED_SOURCE: 'gensrc',
            RoleInGroup.GENERATED_HEADER: 'genhdr',
        }[self]

