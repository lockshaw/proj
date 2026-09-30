from typing import (
    Iterable,
    FrozenSet,
    Iterator,
    Union,
)
from pathlib import PurePath
from ..path_tree import (
    PathTree,
)
from proj.utils import saturating_relative_to
from dataclasses import dataclass
from proj.utils import is_relative_to

@dataclass(frozen=True)
class AllowMask:
    paths: FrozenSet[PurePath]
    extensions: FrozenSet[str]

    def is_allowed(self, p: PurePath) -> bool:
        for _p in self.paths:
            if is_relative_to(p, _p):
                return True
        for _ext in self.extensions:
            if p.name.endswith(_ext):
                return True
        return False

    def restrict_to_subdir(self, p: PurePath) -> 'AllowMask':
        return AllowMask.from_iter(
            paths=[rel for _p in self.paths if (rel := saturating_relative_to(_p, p)) is not None],
            extensions=self.extensions,
        )

    @staticmethod
    def from_iter(*, paths: Iterable[Union[str, PurePath]] = tuple(), extensions: Iterable[str] = tuple()) -> 'AllowMask':
        _extensions = frozenset(extensions)
        for ext in _extensions:
            assert '/' not in ext
            assert ext.startswith('.')

        return AllowMask(
            paths=frozenset([
                PurePath(p) for p in paths
            ]),
            extensions=_extensions,
        )

@dataclass(frozen=True)
class IgnoreMask:
    paths: FrozenSet[PurePath]
    extensions: FrozenSet[str]

    def is_allowed(self, p: PurePath) -> bool:
        for _p in self.paths:
            if is_relative_to(p, _p):
                return False
        for _ext in self.extensions:
            if p.name.endswith(_ext):
                return False
        return True

    def restrict_to_subdir(self, p: PurePath) -> 'IgnoreMask':
        return IgnoreMask.from_iter(
            paths=[rel for _p in self.paths if (rel := saturating_relative_to(_p, p)) is not None],
            extensions=self.extensions,
        )

    @staticmethod
    def from_iter(*, paths: Iterable[Union[str, PurePath]] = tuple(), extensions: Iterable[str] = tuple()) -> 'IgnoreMask':
        _extensions = frozenset(extensions)
        for ext in _extensions:
            assert '/' not in ext
            assert ext.startswith('.')

        return IgnoreMask(
            paths=frozenset([
                PurePath(p) for p in paths
            ]),
            extensions=_extensions,
        )

class MaskedPathTree(PathTree):
    _wrapped: PathTree
    _mask: Union[AllowMask, IgnoreMask]

    def __init__(
        self,
        path_tree: PathTree,
        mask: Union[AllowMask, IgnoreMask],
    ) -> None:
        self._wrapped = path_tree
        self._mask = mask

    @property
    def mask(self) -> Union[AllowMask, IgnoreMask]:
        return self._mask

    def _is_masked(self, p: PurePath) -> bool:
        return not self._mask.is_allowed(p)

    def _filter_masked(self, i: Iterable[PurePath]) -> Iterator[PurePath]:
        for p in i:
            if not self._is_masked(p):
                yield p

    def has_path(self, p: PurePath) -> bool:
        if self._is_masked(p):
            return False
        return self._wrapped.has_path(p=p)

    def has_dir(self, p: PurePath) -> bool:
        if self._is_masked(p):
            return False
        return self._wrapped.has_dir(p=p)

    def ls_dir(self, p: PurePath) -> Iterator[PurePath]:
        return self._filter_masked(self._wrapped.ls_dir(p=p))

    def restrict_to_subdir(self, p: PurePath) -> 'MaskedPathTree':
        return MaskedPathTree(
            path_tree=self._wrapped.restrict_to_subdir(p),
            mask=self._mask.restrict_to_subdir(p),
        )

    def has_file(self, p: PurePath) -> bool:
        if self._is_masked(p):
            return False
        return self.has_file(p=p)

    def with_extension(self, extension: str) -> Iterator[PurePath]:
        return self._filter_masked(self._wrapped.with_extension(extension=extension))

    def files(self) -> Iterator[PurePath]:
        return self._filter_masked(self._wrapped.files())

    def dirs(self) -> Iterator[PurePath]:
        return self._filter_masked(self._wrapped.dirs())

    def __str__(self) -> str:
        return f'MaskedPathTree(_wrapped={self._wrapped}, _mask={self._mask})'
