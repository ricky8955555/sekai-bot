from pathlib import Path
from typing import Awaitable, Callable, Generic, Protocol, TypeVar

from aiofile import async_open


class KeyConvertible(Protocol):
    def as_key(self) -> str:
        ...


_KT = TypeVar("_KT", bound=KeyConvertible | str)

Upstream = Callable[[_KT], Awaitable[bytes]]


class FilesystemStorage(Generic[_KT]):
    path: Path
    upstream: Upstream[_KT]

    def __init__(
        self,
        path: Path,
        upstream: Upstream[_KT],
    ) -> None:
        self.path = path
        self.upstream = upstream

    def _filepath(self, key: _KT) -> Path:
        name = key if isinstance(key, str) else key.as_key()
        return self.path / name

    async def get(self, key: _KT) -> bytes:
        path = self._filepath(key)

        if path.exists():
            async with async_open(path, "rb") as afp:
                return await afp.read()

        data = await self.upstream(key)

        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        async with async_open(path, "wb+") as afp:
            await afp.write(data)

        return data
