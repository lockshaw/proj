from proj.config_file import (
    ProjectConfig,
    get_possible_spec_paths,
)
from pathlib import Path
from typing import (
    Iterator,
)
import itertools


def find_outdated(root: Path, config: ProjectConfig) -> Iterator[Path]:
    for p in itertools.chain(
        root.rglob("**/*.dtg" + config.header_extension),
        root.rglob("**/*.dtg.cc"),
    ):
        if not any(
            possible_spec_path.is_file()
            for possible_spec_path in get_possible_spec_paths(p)
        ):
            yield p
