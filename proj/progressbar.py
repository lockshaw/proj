import logging
from abc import abstractmethod
import contextlib
from typing import (
    Optional,
    Type,
    Any,
)
from types import (
    TracebackType,
)

_l = logging.getLogger(__name__)

try:
    import enlighten  # type: ignore
except ImportError:
    _l.warn(
        "Failed to import enlighten (https://pypi.org/project/enlighten/). "
        "Everything will work fine, but you will be lacking fancy progress bars"
    )
    enlighten = None

EnlightenPB = Any


class ProgressBar(contextlib.AbstractContextManager["ProgressBar"]):
    @abstractmethod
    def update(self, incr: int = 1, force: bool = False) -> None:
        ...


class FakeProgressBar(ProgressBar):
    def update(self, incr: int = 1, force: bool = False) -> None:
        pass

    def __enter__(self) -> "FakeProgressBar":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exec_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        pass


class EnlightenProgressBar(ProgressBar):
    def __init__(self, enlighten_bar: EnlightenPB) -> None:
        self._enlighten_bar = enlighten_bar

    def __enter__(self) -> "EnlightenProgressBar":
        self._enlighten_bar.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        result = self._enlighten_bar.__exit__(exc_type, exc_value, traceback)
        if result is None:
            return result
        else:
            assert isinstance(result, bool)
            return result

    def update(self, incr: int = 1, force: bool = False) -> None:
        self._enlighten_bar.update(incr=incr, force=force)


class ProgressBarManager(contextlib.AbstractContextManager["ProgressBarManager"]):
    @abstractmethod
    def counter(self, total: int, desc: str, unit: Optional[str] = None) -> ProgressBar:
        ...

    @abstractmethod
    def __enter__(self) -> "ProgressBarManager":
        ...


class FakeManager(ProgressBarManager):
    def counter(self, total: int, desc: str, unit: Optional[str] = None) -> ProgressBar:
        return FakeProgressBar()

    def __enter__(self) -> ProgressBarManager:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exec_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        pass


class EnlightenManager(ProgressBarManager):
    def __init__(self) -> None:
        self._enlighten_mgr = enlighten.get_manager()

    def __enter__(self) -> ProgressBarManager:
        self._enlighten_mgr.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        result = self._enlighten_mgr.__exit__(exc_type, exc_value, traceback)
        if result is None:
            return result
        else:
            assert isinstance(result, bool)
            return result

    def counter(self, total: int, desc: str, unit: Optional[str] = None) -> ProgressBar:
        return EnlightenProgressBar(
            self._enlighten_mgr.counter(total=total, desc=desc, unit=unit)
        )


def get_progress_manager() -> ProgressBarManager:
    if enlighten is None:
        return FakeManager()
    else:
        return EnlightenManager()
