from dataclasses import dataclass, field
from pathlib import (
    PurePath,
)
from typing import (
    Union,
    Sequence,
    List,
    Optional,
)
from .absolute_path import AbsolutePath
from .repo import Repo
from proj.utils import is_relative_to

@dataclass(frozen=True)
class RepoRelPath:
    path: PurePath
    repo: Optional[Repo] = field(default=None)

    def is_relative_to(self, other: 'RepoRelPath') -> bool:
        assert self.repo == other.repo and self.repo is not None
        return is_relative_to(self.path, other.path)

    def __truediv__(self, other: Union[str, PurePath]) -> 'RepoRelPath':
        return RepoRelPath(self.path / other, self.repo)

    def with_repo(self, repo: Repo) -> 'RepoRelPath':
        return RepoRelPath(self.path, repo)

    def without_repo(self) -> 'RepoRelPath':
        return RepoRelPath(self.path, None)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def parents(self) -> Sequence['RepoRelPath']:
        return [RepoRelPath(p) for p in self.path.parents]

    @property
    def suffixes(self) -> List[str]:
        return self.path.suffixes
