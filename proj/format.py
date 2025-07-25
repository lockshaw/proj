from pathlib import Path
import logging
import subprocess
from os import PathLike
from typing import (
    Sequence,
    Optional,
    Iterator,
)
from .config_file import ProjectConfig

_l = logging.getLogger(__name__)


def find_files(config: ProjectConfig) -> Iterator[Path]:
    patterns = [f"*{config.header_extension}", "*.cc", "*.cpp", "*.cu", "*.c", "*.decl"]
    blacklist = [
        config.base / "deps",
        config.base / "build",
    ]

    def is_blacklisted(p: Path) -> bool:
        for blacklisted in blacklist:
            if p.is_relative_to(blacklisted):
                return True
        if p.name.endswith(".dtg.cc") or p.name.endswith(
            ".dtg" + config.header_extension
        ):
            return True
        return False

    for pattern in patterns:
        for found in config.base.rglob(pattern):
            if not is_blacklisted(found):
                yield found


def _run_clang_format(
    root: Path,
    args: Sequence[str],
    files: Sequence[PathLike[str]],
    use_default_style: bool = False,
) -> None:
    command = ["ff-clang-format"]
    if not use_default_style:
        style_file = root / ".clang-format-for-format-sh"
        command.append(f"--style=file:{style_file}")
    command += args
    if len(files) == 1:
        _l.debug(f"Running command {command} on 1 file: {files[0]}")
    else:
        _l.debug(f"Running command {command} on {len(files)} files")
    subprocess.check_call(command + [*files], stderr=subprocess.STDOUT)


def run_formatter_check(
    config: ProjectConfig, files: Optional[Sequence[PathLike[str]]] = None
) -> None:
    if files is None:
        files = list(find_files(config=config))
    _l.info("Checking the following files:")
    for f in files:
        _l.info(f"- {f}")
    _run_clang_format(
        root=config.base,
        args=["--dry-run", "--Werror"],
        files=files,
    )


def run_formatter(
    config: ProjectConfig, files: Optional[Sequence[PathLike[str]]] = None
) -> None:
    if files is None:
        files = list(find_files(config=config))
    _l.info("Formatting the following files:")
    for f in files:
        _l.info(f"- {f}")
    _run_clang_format(
        root=config.base,
        args=["-i"],  # in-place
        files=files,
    )
