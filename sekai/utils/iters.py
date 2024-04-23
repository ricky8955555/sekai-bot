from typing import Callable, Iterable, Sequence, TypeVar

_T = TypeVar("_T")
_DT = TypeVar("_DT")


def first(iterable: Iterable[_T], condition: Callable[[_T], bool]) -> _T:
    return next(filter(condition, iterable))


def at(seq: Sequence[_T], index: int, default: _DT = None) -> _T | _DT:
    if len(seq) <= index:
        return default
    return seq[index]
