from .clang_tools import (
    download_tool,
    ClangToolsConfig,
    Tool,
    TOOL_CONFIGS,
    System,
    Arch,
)
from pathlib import Path
from os import PathLike
import logging
from typing import (
    Sequence,
    Optional,
    Iterator,
)
import subprocess
from .config_file import ProjectConfig

_l = logging.getLogger(__name__)

def find_files(root: Path, config: ProjectConfig) -> Iterator[Path]:
    #patterns = [f'*{config.header_extension}', '*.cc', '*.cpp', '*.cu', '*.c', '*.decl']
    patterns = ['*.cc', '*.cpp', '*.cu', '*.c']
    blacklist = [
        root / 'lib' / 'runtime',
        root / 'lib' / 'kernels',
    ]
    whitelist = [
        root / 'lib',
    ]
    
    def is_blacklisted(p: Path) -> bool:
        if not any(p.is_relative_to(whitelisted) for whitelisted in whitelist):
            return True
        if any(p.is_relative_to(blacklisted) for blacklisted in blacklist):
            return True
        if any(parent.name == 'test' for parent in p.parents if parent.is_relative_to(root)):
            return True
        if '.dtg' in p.suffixes:
            return True
        return False

    for pattern in patterns:
        for found in root.rglob(pattern):
            if not is_blacklisted(found):
                yield found

def _run_clang_tidy(
    root: Path, config: ClangToolsConfig, args: Sequence[str], files: Sequence[PathLike[str]], use_default_config: bool = False,
    profile_checks: bool = False,
) -> None:

    command = [str(config.clang_tool_binary_path(Tool.clang_tidy))]
    if not use_default_config:
        config_rel_path = config.config_file_for_tool(Tool.clang_tidy)
        assert config_rel_path is not None
        config_abs_path = root / config_rel_path
        _l.debug(f"clang-tidy config should be located at {config_abs_path}")
        assert config_abs_path.is_file()

        command.append(f'--config-file={config_abs_path}')
    if profile_checks:
        command.append('--enable-check-profile')

    command += args

    if len(files) == 1:
        _l.debug(f"Running command {command} on 1 file: {files[0]}")
    else:
        _l.debug(f"Running command {command} on {len(files)} files")
    subprocess.check_call(command + [*files], stderr=subprocess.STDOUT)

def run_linter(root: Path, config: ProjectConfig, files: Optional[Sequence[PathLike[str]]] = None, profile_checks: bool = False) -> None:
    if files is None:
        files = list(find_files(root=root, config=config))
    tools_config = ClangToolsConfig(
        tools_dir=root / '.tools',
        tool_configs=TOOL_CONFIGS,
        system=System.get_current(),
        arch=Arch.get_current(),
    )
    download_tool(
        tool=Tool.clang_tidy,
        config=tools_config,
    )
    _l.info('Linting the following files:')
    for f in files:
        _l.info(f'- {f}')
    _run_clang_tidy(
        root=root,
        config=tools_config,
        args=[
            '-p', 
            str(root / 'compile_commands.json'),
            '--header-filter',
            f'^{root}/.*$',
        ],
        files=files,
        profile_checks=profile_checks,
    )
