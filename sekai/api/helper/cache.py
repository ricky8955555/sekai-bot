import asyncio
from asyncio import Lock
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterable, Callable, Generic, cast

from aiofile import async_open
from pydantic import BaseModel

from sekai.api import MasterApi
from sekai.api.exc import ObjectNotFound
from sekai.core.models import AnySharedModel, SharedModel
from sekai.core.models.card import CardInfo
from sekai.core.models.chara import (
    Character,
    CharacterInfo,
    CharacterType,
    ExtraCharacter,
    GameCharacter,
)
from sekai.core.models.live import LiveInfo
from sekai.core.models.music import MusicInfo, MusicVersion


class Cache(BaseModel, Generic[AnySharedModel]):
    data: list[AnySharedModel]
    last: datetime


@dataclass(frozen=True)
class CachingStrategy:
    expiry: timedelta = timedelta(days=1)
    write_in_background: bool = True


class CachingMasterApi(MasterApi):
    path: Path
    upstream: MasterApi
    strategy: CachingStrategy
    _cache: dict[type[SharedModel], Cache[Any]]  # it is okay to iterate to find one
    _locks: dict[type[SharedModel], Lock]

    def __init__(
        self, upstream: MasterApi, cache_path: Path, strategy: CachingStrategy | None = None
    ) -> None:
        self.upstream = upstream
        self.path = cache_path
        self.strategy = strategy or CachingStrategy()
        self._cache = {}
        self._locks = {}

    def _expired(self, cache: Cache[AnySharedModel]) -> bool:
        return (datetime.now() - cache.last) > self.strategy.expiry

    async def _get_cache(self, type: type[AnySharedModel]) -> Cache[AnySharedModel] | None:
        if (cached := self._cache.get(type)) is not None:
            return cached
        path = (self.path / type.__name__).with_suffix(".json")
        if not path.exists():
            return None
        assert path.is_file(), f"{path} is not a file."
        async with async_open(path, "r") as afp:
            data = await afp.read()
        wrapped_type = cast(Cache[AnySharedModel], Cache.__class_getitem__(type))
        cache = wrapped_type.model_validate_json(data)
        self._cache[type] = cache
        return cache

    async def _set_cache(self, models: list[AnySharedModel]) -> Cache[AnySharedModel]:
        async def write():
            data = cache.model_dump_json()
            async with async_open(path, "w") as afp:
                await afp.write(data)

        assert models, "no model given."
        typ = type(models[0])
        path = (self.path / typ.__name__).with_suffix(".json")
        assert not path.exists() or path.is_file(), f"{path} is not a file."
        cache = Cache(data=models, last=datetime.now())
        task = asyncio.create_task(write())
        if not self.strategy.write_in_background:
            await task
        self._cache[typ] = cache
        return cache

    async def _get_or_fetch_models(
        self, type: type[AnySharedModel], upstream: AsyncIterable[AnySharedModel]
    ) -> AsyncIterable[AnySharedModel]:
        lock = self._locks.setdefault(type, Lock())
        try:
            await lock.acquire()
            if not (cache := await self._get_cache(type)) or self._expired(cache):
                models = [model async for model in upstream]
                cache = await self._set_cache(models)
        finally:
            lock.release()
        for model in cache.data:
            yield model

    async def _get_model(
        self, iterator: AsyncIterable[AnySharedModel], condition: Callable[[AnySharedModel], bool]
    ) -> AnySharedModel:
        async for model in iterator:
            if condition(model):
                return model
        raise ObjectNotFound

    async def _get_models(
        self, iterator: AsyncIterable[AnySharedModel], condition: Callable[[AnySharedModel], bool]
    ) -> list[AnySharedModel]:
        models = [model async for model in iterator if condition(model)]
        if not models:
            raise ObjectNotFound
        return models

    def iter_card_infos(self) -> AsyncIterable[CardInfo]:
        return self._get_or_fetch_models(CardInfo, self.upstream.iter_card_infos())

    async def get_card_info(self, id: int) -> CardInfo:
        return await self._get_model(self.iter_card_infos(), lambda model: model.id == id)

    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        raise NotImplementedError

    def iter_game_characters(self) -> AsyncIterable[GameCharacter]:
        return self._get_or_fetch_models(GameCharacter, self.upstream.iter_game_characters())

    async def get_game_character(self, id: int) -> GameCharacter:
        return await self._get_model(self.iter_game_characters(), lambda model: model.id == id)

    def iter_extra_characters(self) -> AsyncIterable[ExtraCharacter]:
        return self._get_or_fetch_models(ExtraCharacter, self.upstream.iter_extra_characters())

    async def get_extra_character(self, id: int) -> ExtraCharacter:
        return await self._get_model(self.iter_extra_characters(), lambda model: model.id == id)

    async def iter_character_infos(self) -> AsyncIterable[CharacterInfo]:
        async for model in self.iter_game_characters():
            yield model
        async for model in self.iter_extra_characters():
            yield model

    async def get_character_info(self, character: Character) -> CharacterInfo:
        match character.type:
            case CharacterType.GAME:
                return await self.get_game_character(character.id)
            case CharacterType.EXTRA:
                return await self.get_extra_character(character.id)

    def iter_music_infos(self) -> AsyncIterable[MusicInfo]:
        return self._get_or_fetch_models(MusicInfo, self.upstream.iter_music_infos())

    async def get_music_info(self, id: int) -> MusicInfo:
        return await self._get_model(self.iter_music_infos(), lambda model: model.id == id)

    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        raise NotImplementedError

    def iter_music_versions(self) -> AsyncIterable[MusicVersion]:
        return self._get_or_fetch_models(MusicVersion, self.upstream.iter_music_versions())

    async def get_music_version(self, id: int) -> MusicVersion:
        return await self._get_model(self.iter_music_versions(), lambda model: model.id == id)

    async def get_versions_of_music(self, id: int) -> list[MusicVersion]:
        return await self._get_models(
            self.iter_music_versions(), lambda model: model.music_id == id
        )

    def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        return self._get_or_fetch_models(LiveInfo, self.upstream.iter_live_infos())

    async def get_live_info(self, id: int) -> LiveInfo:
        return await self._get_model(self.iter_live_infos(), lambda model: model.id == id)

    async def get_live_infos_of_music(self, id: int) -> list[LiveInfo]:
        return await self._get_models(self.iter_live_infos(), lambda model: model.music_id == id)
