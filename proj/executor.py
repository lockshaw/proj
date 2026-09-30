from typing import (
    TypeVar,
    Set,
    List,
    Iterator,
    Tuple,
    Callable,
    Sequence,
    Dict,
    Optional,
)
from enum import (
    Enum,
    auto,
)
from dataclasses import dataclass
import concurrent.futures
from .progressbar import (
    get_progress_manager,
)
from . import subprocess_trace as subprocess
from pathlib import Path
from .utils import (
    default_to,
)
import logging

_l = logging.getLogger(__name__)

@dataclass(frozen=True, eq=True)
class Task:
    cmd: List[str]
    cwd: Path
    env: Dict[str, str]
    timeout_seconds: Optional[float]

class TerminationType(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    TIMEOUT = auto()

@dataclass(frozen=True, eq=True)
class TaskResult:
    termination: TerminationType
    stderr: bytes
    stdout: bytes

T = TypeVar('T')

def execute_task(args: Task) -> TaskResult:
    try:
        completed_process = subprocess.run(
            command=args.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=args.cwd,
            env=args.env,
            timeout=args.timeout_seconds,
        )
    except subprocess.TimeoutExpired as e:
        return TaskResult(
            termination=TerminationType.TIMEOUT,
            stderr=default_to(e.stderr, b''),
            stdout=default_to(e.stdout, b''),
        )

    return TaskResult(
        termination=(
            TerminationType.SUCCESS
            if completed_process.returncode == 0
            else TerminationType.FAILURE
        ),
        stderr=completed_process.stderr,
        stdout=completed_process.stdout,
    )

def execute_tasks(
    task_type_name_plural: str,
    compile_task: Callable[[T], Task],
    tasks: Sequence[T],
    num_jobs: int,
) -> Iterator[Tuple[T, TaskResult]]:
    done: Set[T] = set()

    def log_outstanding_tasks(elide_at: int = 3) -> None:
        not_completed = [
            j for j in tasks if j not in done
        ]

        message_lines = [
            f'Waiting on {len(not_completed)} {task_type_name_plural}:',
            *[
                '- ' + repr(tc)
                for tc in not_completed[:elide_at]
            ],
        ]
        if len(not_completed) > elide_at:
            not_shown = len(not_completed) - elide_at
            message_lines.append(
                f'and {not_shown} others'
            )

        message = '\n'.join(message_lines)
        _l.info(message)

    manager = get_progress_manager()
    with manager.counter(total=len(tasks), desc=f"Running {task_type_name_plural}") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_jobs) as executor:
            future_to_task = {
                executor.submit(
                    execute_task,
                    compile_task(task),
                ): task
                for task in tasks
            }
            log_outstanding_tasks()

            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                _l.debug(
                    'Task %s finished running.',
                    task,
                )

                try:
                    task_result = future.result()
                except Exception:
                    _l.exception('Encountered an exception')
                else:
                    pbar.update()

                done.add(task)
                log_outstanding_tasks()

                yield (task, task_result)
