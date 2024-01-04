import asyncio
from pathlib import Path
from typing import Generic, Mapping, TypeVar, cast

from aiofile import async_open
from pydantic import BaseModel, RootModel

from sekai.bot.storage import StorageStrategy

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_DT = TypeVar("_DT")


class _PairModel(BaseModel, Generic[_KT, _VT]):
    k: _KT
    v: _VT


class _MappingData(RootModel[list[_PairModel[_KT, _VT]]], Generic[_KT, _VT]):
    pass


class MappingDataStorage(Generic[_KT, _VT]):
    path: Path
    strategy: StorageStrategy
    _mapping: dict[_KT, _VT] | None
    _model: type[_VT]
    _mapping_data_type: type[_MappingData[_KT, _VT]]

    def __init__(
        self,
        key: type[_KT],
        value: type[_VT],
        path: Path,
        strategy: StorageStrategy | None = None,
    ) -> None:
        self.path = path if path.suffix else path.with_suffix(".json")
        self.strategy = strategy or StorageStrategy()
        self._mapping = None
        self._mapping_data_type = cast(
            type[_MappingData[_KT, _VT]], _MappingData.__class_getitem__((key, value))
        )

    async def _load_file(self) -> dict[_KT, _VT]:
        if not self.path.exists():
            self._mapping = {}
            return self._mapping
        async with async_open(self.path, "r") as afp:
            data = await afp.read()
        pairs = self._mapping_data_type.model_validate_json(data)
        self._mapping = {model.k: model.v for model in pairs.root}
        return self._mapping

    async def _write_file(self) -> None:
        async def write():
            dumped = data.model_dump_json()
            async with async_open(self.path, "w") as afp:
                await afp.write(dumped)

        if not self._mapping:
            return
        pairs = [_PairModel(k=k, v=v) for k, v in self._mapping.items()]
        data = _MappingData(root=pairs)
        task = asyncio.create_task(write())
        if not self.strategy.write_in_background:
            await task

    async def _load_ref(self) -> dict[_KT, _VT]:
        if self._mapping is not None:
            return self._mapping
        mapping = await self._load_file()
        return mapping

    async def load(self) -> dict[_KT, _VT]:
        mapping = await self._load_ref()
        return dict(mapping)

    async def write(self, mapping: Mapping[_KT, _VT]) -> None:
        self._mapping = dict(mapping)
        await self._write_file()

    async def get(self, key: _KT, default: _DT = None) -> _VT | _DT:
        mapping = await self._load_ref()
        return mapping.get(key, default)

    async def update(self, key: _KT, value: _VT) -> None:
        mapping = await self._load_ref()
        mapping[key] = value
        await self._write_file()
