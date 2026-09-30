from .clang_tools import (
    download_tool,
    ClangToolsConfig,
    Tool,
    TOOL_CONFIGS,
    System,
    Arch,
)
from pathlib import Path, PurePath
from os import PathLike
import logging
from typing import (
    Sequence,
    Optional,
    Iterator,
)
import subprocess
from .paths import (
    RepoRelPath,
    Repo,
)
from .config_file import (
    ExtensionConfig,
)
from .trees import PathTree
from .subprocess_invocation import SubprocessInvocation
from proj.utils import is_relative_to

_l = logging.getLogger(__name__)


def find_repo_files_for_linter(repo_path_tree: PathTree, extension_config: ExtensionConfig) -> Iterator[RepoRelPath]:
    extensions = [extension_config.src_extension, ".cpp", ".cu", ".c"]
    blacklist = [
        RepoRelPath(PurePath("lib")) / "runtime",
        RepoRelPath(PurePath("lib")) / "kernels",
    ]
    whitelist = [
        RepoRelPath(PurePath("lib")),
    ]

    def is_blacklisted(p: RepoRelPath) -> bool:
        if not any(p.is_relative_to(whitelisted) for whitelisted in whitelist):
            return True
        if any(p.is_relative_to(blacklisted) for blacklisted in blacklist):
            return True
        if any(
            parent.name == "test" for parent in p.parents
        ):
            return True
        if ".dtg" in p.suffixes:
            return True
        return False

    for extension in extensions:
        for found in repo_path_tree.with_extension(extension):
            if not is_blacklisted(RepoRelPath(found)):
                yield RepoRelPath(found)


def _run_clang_tidy(
    root: Path,
    config: ClangToolsConfig,
    args: Sequence[str],
    files: Sequence['PathLike[str]'],
    use_default_config: bool = False,
    profile_checks: bool = False,
) -> SubprocessInvocation:
    command = [str(config.clang_tool_binary_path(Tool.clang_tidy))]
    if not use_default_config:
        config_rel_path = config.config_file_for_tool(Tool.clang_tidy)
        assert config_rel_path is not None
        config_abs_path = root / config_rel_path
        _l.debug(f"clang-tidy config should be located at {config_abs_path}")
        assert config_abs_path.is_file()

        command.append(f"--config-file={config_abs_path}")
    if profile_checks:
        command.append("--enable-check-profile")

    command += args

    if len(files) == 1:
        _l.debug(f"Running command {command} on 1 file: {files[0]}")
    else:
        _l.debug(f"Running command {command} on {len(files)} files")
    return SubprocessInvocation(
        cmd=command + list(map(str, files)),
        stderr=subprocess.STDOUT,
    )


def run_linter(
    repo: Repo,
    repo_path_tree: PathTree,
    extension_config: ExtensionConfig,
    files: Optional[Sequence['PathLike[str]']] = None,
    profile_checks: bool = False,
) -> None:
    if files is None:
        files = [f.path for f in find_repo_files_for_linter(repo_path_tree, extension_config)]
    tools_config = ClangToolsConfig(
        tools_dir=Path(repo.path / ".tools"),
        tool_configs=TOOL_CONFIGS,
        system=System.get_current(),
        arch=Arch.get_current(),
    )
    download_tool(
        tool=Tool.clang_tidy,
        config=tools_config,
    )
    _l.info("Linting the following files:")
    for f in files:
        _l.info(f"- {f}")
    _run_clang_tidy(
        root=Path(repo.path),
        config=tools_config,
        args=[
            "-p",
            str(repo.path / "compile_commands.json"),
            "--header-filter",
            f"^{repo.path}/.*$",
        ],
        files=files,
        profile_checks=profile_checks,
    ).check_call()
