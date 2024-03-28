import asyncio
import shutil
from asyncio import Lock, Queue
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterable, Protocol, TypeVar

from aiofile import async_open
from pydantic import RootModel

from sekai.api import MasterApi
from sekai.api.exc import ObjectNotFound
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


class IdModel(Protocol):
    id: int


AnyIdModel = TypeVar("AnyIdModel", bound=IdModel)


@dataclass(frozen=True)
class CachingStrategy:
    expiry: timedelta = timedelta(days=1)


class CachingMasterApi(MasterApi):
    path: Path
    upstream: MasterApi
    strategy: CachingStrategy
    _locks: dict[type[IdModel], Lock]

    def __init__(
        self, upstream: MasterApi, cache_path: Path, strategy: CachingStrategy | None = None
    ) -> None:
        self.upstream = upstream
        self.path = cache_path
        self.strategy = strategy or CachingStrategy()
        self._locks = dict()

    def _models_path(self, typ: type[AnyIdModel]) -> Path:
        return self.path / typ.__name__
    
    def _cache_path(self, typ: type[AnyIdModel], id: int) -> Path:
        return (self._models_path(typ) / str(id)).with_suffix(".json")

    def _updated_mark_path(self, typ: type[AnyIdModel]) -> Path:
        return self._models_path(typ) / ".last"

    def _expired(self, typ: type[AnyIdModel]) -> bool:
        path = self._updated_mark_path(typ)
        if not path.exists():
            return True
        return (
            datetime.now() - datetime.fromtimestamp(path.stat().st_atime)
        ) > self.strategy.expiry

    def _mark_updated(self, typ: type[AnyIdModel]) -> None:
        path = self._updated_mark_path(typ)
        path.touch()

    async def _get_cache(self, typ: type[AnyIdModel], id: int) -> AnyIdModel | None:
        path = self._cache_path(typ, id)
        if not path.exists():
            return None
        assert path.is_file(), f"{path} is not a file."
        async with async_open(path, "r") as afp:
            data = await afp.read()
        wrapped_type = RootModel.__class_getitem__(typ)
        cache = wrapped_type.model_validate_json(data)  # type: ignore
        return cache.root  # type: ignore

    async def _iter_caches(self, typ: type[AnyIdModel]) -> AsyncIterable[AnyIdModel]:
        path = self._models_path(typ)
        if not path.exists():
            return
        for file in path.iterdir():
            if file.suffix != ".json":
                continue
            async with async_open(file, "r") as afp:
                data = await afp.read()
            wrapped_type = RootModel.__class_getitem__(typ)
            cache = wrapped_type.model_validate_json(data)  # type: ignore
            yield cache.root  # type: ignore

    async def _sync_models(
        self, typ: type[AnyIdModel], models: AsyncIterable[AnyIdModel]
    ) -> AsyncIterable[AnyIdModel]:
        async def worker() -> None:
            await lock.acquire()
            try:
                parent = self._models_path(typ)
                shutil.rmtree(parent, ignore_errors=True)
                parent.mkdir(parents=True)
                async for model in models:
                    queue.put_nowait(model)
                    path = self._cache_path(typ, model.id).with_suffix(".json")
                    wrapped = RootModel(root=model)
                    data = wrapped.model_dump_json()
                    async with async_open(path, "w") as afp:
                        await afp.write(data)
                self._mark_updated(typ)
            finally:
                lock.release()
                queue.put_nowait(None)

        lock = self._locks.setdefault(typ, Lock())

        if lock.locked():
            await lock.acquire()
            lock.release()
            async for model in self._get_or_fetch_models(typ, models):
                yield model
            return

        queue = Queue[AnyIdModel | None]()
        asyncio.create_task(worker())
        while True:
            model = await queue.get()
            if not model:
                return
            yield model

    async def _get_or_fetch_model(
        self, typ: type[AnyIdModel], id: int, upstream: AsyncIterable[AnyIdModel]
    ) -> AnyIdModel:
        model = await self._get_cache(typ, id)
        if self._expired(typ):
            async for model in self._sync_models(typ, upstream):
                if model.id == id:
                    return model
        if not model:
            raise ObjectNotFound
        return model

    def _get_or_fetch_models(
        self, typ: type[AnyIdModel], upstream: AsyncIterable[AnyIdModel]
    ) -> AsyncIterable[AnyIdModel]:
        if self._expired(typ):
            return self._sync_models(typ, upstream)
        return self._iter_caches(typ)

    def iter_card_infos(self) -> AsyncIterable[CardInfo]:
        return self._get_or_fetch_models(CardInfo, self.upstream.iter_card_infos())

    async def get_card_info(self, id: int) -> CardInfo:
        return await self._get_or_fetch_model(CardInfo, id, self.upstream.iter_card_infos())

    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        raise NotImplementedError

    def iter_game_characters(self) -> AsyncIterable[GameCharacter]:
        return self._get_or_fetch_models(GameCharacter, self.upstream.iter_game_characters())

    async def get_game_character(self, id: int) -> GameCharacter:
        return await self._get_or_fetch_model(
            GameCharacter, id, self.upstream.iter_game_characters()
        )

    def iter_extra_characters(self) -> AsyncIterable[ExtraCharacter]:
        return self._get_or_fetch_models(ExtraCharacter, self.upstream.iter_extra_characters())

    async def get_extra_character(self, id: int) -> ExtraCharacter:
        return await self._get_or_fetch_model(
            ExtraCharacter, id, self.upstream.iter_extra_characters()
        )

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
        return await self._get_or_fetch_model(MusicInfo, id, self.upstream.iter_music_infos())

    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        raise NotImplementedError

    def iter_music_versions(self) -> AsyncIterable[MusicVersion]:
        return self._get_or_fetch_models(MusicVersion, self.upstream.iter_music_versions())

    async def get_music_version(self, id: int) -> MusicVersion:
        return await self._get_or_fetch_model(MusicVersion, id, self.upstream.iter_music_versions())

    async def iter_versions_of_music(self, id: int) -> AsyncIterable[MusicVersion]:
        async for version in self.iter_music_versions():
            if version.music_id == id:
                yield version

    def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        return self._get_or_fetch_models(LiveInfo, self.upstream.iter_live_infos())

    async def get_live_info(self, id: int) -> LiveInfo:
        return await self._get_or_fetch_model(LiveInfo, id, self.upstream.iter_live_infos())

    async def iter_live_infos_of_music(self, id: int) -> AsyncIterable[LiveInfo]:
        async for info in self.iter_live_infos():
            if info.music_id == id:
                yield info
