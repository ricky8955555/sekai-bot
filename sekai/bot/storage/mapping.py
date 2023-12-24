import asyncio
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Mapping, TypeVar, cast

from aiofile import async_open
from pydantic import BaseModel, RootModel

_T_Key = TypeVar("_T_Key")
_T_Value = TypeVar("_T_Value")
_T_Default = TypeVar("_T_Default")


@dataclass(frozen=True)
class StorageStrategy:
    write_in_background: bool = True


class _PairModel(BaseModel, Generic[_T_Key, _T_Value]):
    k: _T_Key
    v: _T_Value


class _MappingData(RootModel[list[_PairModel[_T_Key, _T_Value]]], Generic[_T_Key, _T_Value]):
    pass


class MappingDataStorage(Generic[_T_Key, _T_Value]):
    path: Path
    strategy: StorageStrategy
    _mapping: dict[_T_Key, _T_Value] | None
    _model: type[_T_Value]

    def __init__(self, path: Path, strategy: StorageStrategy | None = None) -> None:
        self.path = path if path.suffix else path.with_suffix(".json")
        self.strategy = strategy or StorageStrategy()
        self._mapping = None

    @property
    def _mapping_data_type(self) -> type[_MappingData[_T_Key, _T_Value]]:
        assert (cls := getattr(self, "__orig_class__")), "no '__orig_class__' found."
        assert len(types := typing.get_args(cls)) == 2, "unsatisfied generics got."
        return cast(type[_MappingData[_T_Key, _T_Value]], _MappingData.__class_getitem__(types))

    async def _load_file(self) -> dict[_T_Key, _T_Value]:
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

    async def _load_ref(self) -> dict[_T_Key, _T_Value]:
        if self._mapping is not None:
            return self._mapping
        mapping = await self._load_file()
        return mapping

    async def load(self) -> dict[_T_Key, _T_Value]:
        mapping = await self._load_ref()
        return dict(mapping)

    async def write(self, mapping: Mapping[_T_Key, _T_Value]) -> None:
        self._mapping = dict(mapping)
        await self._write_file()

    async def get(self, key: _T_Key, default: _T_Default = None) -> _T_Value | _T_Default:
        mapping = await self._load_ref()
        return mapping.get(key, default)

    async def update(self, key: _T_Key, value: _T_Value) -> None:
        mapping = await self._load_ref()
        mapping[key] = value
        await self._write_file()
