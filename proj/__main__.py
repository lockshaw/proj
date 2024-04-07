from pathlib import Path
from typing import (
    Any,
    Sequence,
)
import subprocess
import os
import shutil
import multiprocessing
import shlex
import sys
from .config_file import (
    find_config_root,
    get_config,
)
from .dtgen import run_dtgen
from .format import run_formatter
import proj.fix_compile_commands as fix_compile_commands
import logging
from dataclasses import dataclass

_l = logging.getLogger(name='proj')

DIR = Path(__file__).resolve().parent

def main_root(args: Any) -> None:
    config_root = find_config_root(args.path)
    if config_root is not None:
        print(config_root)
    else:
        _l.error('ERROR: Could not find config root')
        _l.error('Exiting unsuccessfully...')
        exit(1)

def subprocess_check_call(command, **kwargs):
    if kwargs.get('shell', False):
        pretty_cmd = ' '.join(command)
        _l.info(f'+++ $ {pretty_cmd}')
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f'+++ $ {pretty_cmd}')
        subprocess.check_call(command, **kwargs)

def subprocess_run(command, **kwargs):
    if kwargs.get('shell', False):
        pretty_cmd = ' '.join(command)
        _l.info(f'+++ $ {pretty_cmd}')
        subprocess.check_call(pretty_cmd, **kwargs)
    else:
        pretty_cmd = shlex.join(command)
        _l.info(f'+++ $ {pretty_cmd}')
        subprocess.check_call(command, **kwargs)

@dataclass(frozen=True)
class MainCmakeArgs:
    path: Path
    force: bool
    trace: bool

def main_cmake(args: MainCmakeArgs) -> None:
    config = get_config(args.path)
    assert config is not None
    if args.force and config.build_dir.exists():
        shutil.rmtree(config.build_dir)
    config.build_dir.mkdir(exist_ok=True, parents=True)
    cmake_args = [f'-D{k}={v}' for k, v in config.cmake_flags.items()]
    cmake_args += shlex.split(os.environ.get('CMAKE_FLAGS', ''))
    if args.trace:
        cmake_args += ['--trace', '--trace-expand', '--trace-redirect=trace.log']
    subprocess_check_call([
        'cmake',
        *cmake_args,
        '..',
    ], stderr=sys.stdout, cwd=config.build_dir, env=os.environ, shell=config.cmake_require_shell)
    COMPILE_COMMANDS_FNAME = 'compile_commands.json'
    if config.fix_compile_commands:
        fix_compile_commands.fix_file(
            compile_commands=config.build_dir / COMPILE_COMMANDS_FNAME, 
            base_dir=config.base,
        )

    with (config.base / COMPILE_COMMANDS_FNAME).open('w') as f:
        subprocess_check_call([
            'compdb',
            '-p',
            '.',
            'list',
        ], stdout=f, cwd=config.build_dir, env=os.environ)

@dataclass(frozen=True)
class MainBuildArgs:
    path: Path
    verbose: bool
    jobs: int

def main_build(args: MainBuildArgs) -> None:
    config = get_config(args.path)
    assert config is not None
    subprocess_check_call([
        'make', '-j', str(args.jobs), *config.build_targets,
    ], env={
        **os.environ, 
        'CCACHE_BASEDIR': str(DIR.parent.parent.parent),
        **({'VERBOSE': '1'} if args.verbose else {})
    }, stderr=sys.stdout, cwd=config.build_dir)

@dataclass(frozen=True)
class MainTestArgs:
    path: Path
    verbose: bool
    jobs: int

def main_test(args: MainTestArgs) -> None:
    config = get_config(args.path)
    assert config is not None
    subprocess_check_call([
        'make', '-j', str(args.jobs), *config.test_targets,
    ], env={
        **os.environ, 
        'CCACHE_BASEDIR': str(DIR.parent.parent.parent),
        **({'VERBOSE': '1'} if args.verbose else {})
    }, stderr=sys.stdout, cwd=config.build_dir)
    target_regex = '^' + '|'.join(config.test_targets) + '$'
    subprocess_run([
        'ctest', 
        '--progress',
        '--output-on-failure',
        '-L',
        target_regex,
    ], stderr=sys.stdout, cwd=config.build_dir, env=os.environ)

def main_format(args: Any) -> None:
    root = find_config_root(args.path)
    assert root is not None
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_formatter(root, files)

@dataclass(frozen=True)
class MainDtgenArgs:
    path: Path
    files: Sequence[Path]

def main_dtgen(args: MainDtgenArgs) -> None:
    root = find_config_root(args.path)
    assert root is not None
    config = get_config(args.path)
    assert config is not None
    if len(args.files) == 0:
        files = None
    else:
        for file in args.files:
            assert file.is_file()
        files = list(args.files)
    run_dtgen(
        root=root,
        config=config,
        files=files,
    )
    
def main() -> None:
    import argparse 

    logging.basicConfig(level=logging.INFO)

    p = argparse.ArgumentParser()
    subparsers = p.add_subparsers()

    root_p = subparsers.add_parser('root')
    root_p.set_defaults(func=main_root)
    root_p.add_argument('--path', '-p', type=Path, default=Path.cwd())

    test_p = subparsers.add_parser('test')
    test_p.set_defaults(func=main_test)
    test_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    test_p.add_argument('--verbose', '-v', action='store_true')
    test_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())

    build_p = subparsers.add_parser('build')
    build_p.set_defaults(func=main_build)
    build_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    build_p.add_argument('--verbose', '-v', action='store_true')
    build_p.add_argument('--jobs', '-j', type=int, default=multiprocessing.cpu_count())

    cmake_p = subparsers.add_parser('cmake')
    cmake_p.set_defaults(func=main_cmake)
    cmake_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    cmake_p.add_argument('--force', '-f', action='store_true')
    cmake_p.add_argument('--trace', action='store_true')

    dtgen_p = subparsers.add_parser('dtgen')
    dtgen_p.set_defaults(func=main_dtgen)
    dtgen_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    dtgen_p.add_argument('files', nargs='*', type=Path)

    format_p = subparsers.add_parser('format')
    format_p.set_defaults(func=main_format)
    format_p.add_argument('--path', '-p', type=Path, default=Path.cwd())
    format_p.add_argument('files', nargs='*', type=Path)

    args = p.parse_args()
    if hasattr(args, 'func') and args.func is not None:
        args.func(args)
    else:
        p.print_help()
        exit(1)

if __name__ == '__main__':
    main()
