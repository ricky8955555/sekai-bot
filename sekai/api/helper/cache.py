import asyncio
import shutil
from asyncio import Event
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterable, Callable, Generic, Protocol, TypeVar

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
_Updater = Callable[[], AsyncIterable[AnyIdModel]]


@dataclass(frozen=True)
class CachingStrategy:
    expiry: timedelta = timedelta(days=1)


class _CacheManager(Generic[AnyIdModel]):
    path: Path
    strategy: CachingStrategy
    _type: type[AnyIdModel]
    _cached: list[int]
    _sync: Event | None
    _updater: _Updater[AnyIdModel]

    def __init__(
        self,
        path: Path,
        typ: type[AnyIdModel],
        strategy: CachingStrategy,
        updater: _Updater[AnyIdModel],
    ) -> None:
        self.path = path
        self.strategy = strategy
        self._type = typ
        self._sync = None
        self._cached = []
        self._updater = updater

    @property
    def _cached_path(self) -> Path:
        return self.path / ".cached"

    def _cache_path(self, id: int) -> Path:
        return (self.path / str(id)).with_suffix(".json")

    async def _update_cached(self) -> None:
        async with async_open(self._cached_path, "w") as afp:
            await afp.write("\n".join(map(str, self._cached)))

    def _expired(self) -> bool:
        if not self._cached_path.exists():
            return True
        return (
            datetime.now() - datetime.fromtimestamp(self._cached_path.stat().st_mtime)
        ) > self.strategy.expiry

    async def _get_cache(self, id: int) -> AnyIdModel:
        path = self._cache_path(id)
        async with async_open(path, "r") as afp:
            data = await afp.read()
        wrapped_type = RootModel.__class_getitem__(self._type)
        cache = wrapped_type.model_validate_json(data)  # type: ignore
        return cache.root  # type: ignore

    async def _iter_caches(self) -> AsyncIterable[AnyIdModel]:
        for id in self._cached:
            model = await self._get_cache(id)
            assert model, f"id '{id}' was marked as 'cached' but not found."
            yield model

    async def _load_cached(self) -> None:
        async with async_open(self._cached_path, "r") as afp:
            data = await afp.read()
        self._cached = list(map(int, data.splitlines()))

    async def _sync_models(self) -> None:
        async def task() -> None:
            try:
                models = self._updater()
                async for model in models:
                    path = self._cache_path(model.id)
                    wrapped = RootModel(root=model)
                    data = wrapped.model_dump_json()
                    async with async_open(path, "w") as afp:
                        await afp.write(data)
                    self._cached.append(model.id)
                    event.set()
                    event.clear()
                await self._update_cached()
            finally:
                self._sync = None
                event.set()
                event.clear()

        assert self._sync is None, "another task is working."
        shutil.rmtree(self.path, ignore_errors=True)
        self.path.mkdir(parents=True)
        self._sync = event = Event()
        self._cached.clear()
        asyncio.create_task(task())

    async def _iter_syncings(self) -> AsyncIterable[int]:
        assert self._sync is not None, "no sync task is working."
        last = 0
        while True:
            for id in self._cached[last:]:
                yield id
            if not self._sync:
                return
            last = len(self._cached)
            await self._sync.wait()

    async def _iter_syncing_models(self) -> AsyncIterable[AnyIdModel]:
        async for id in self._iter_syncings():
            yield await self._get_cache(id)

    async def _check_cached(self) -> None:
        if not self._cached and self._cached_path.exists():
            await self._load_cached()

    async def iter(self) -> AsyncIterable[AnyIdModel]:
        await self._check_cached()
        if self._expired():
            if not self._sync:
                await self._sync_models()
            it = self._iter_syncing_models()
        else:
            it = self._iter_caches()
        async for model in it:
            yield model

    async def get(self, id: int) -> AnyIdModel:
        await self._check_cached()
        if self._expired():
            if not self._sync:
                await self._sync_models()
            async for cur in self._iter_syncings():
                if cur == id:
                    break
        if id not in self._cached:
            raise ObjectNotFound
        return await self._get_cache(id)


class CachingMasterApi(MasterApi):
    path: Path
    strategy: CachingStrategy
    _card_infos: _CacheManager[CardInfo]
    _game_characters: _CacheManager[GameCharacter]
    _extra_characters: _CacheManager[ExtraCharacter]
    _music_infos: _CacheManager[MusicInfo]
    _music_versions: _CacheManager[MusicVersion]
    _live_infos: _CacheManager[LiveInfo]

    def __init__(
        self, upstream: MasterApi, cache_path: Path, strategy: CachingStrategy | None = None
    ) -> None:
        self.path = cache_path
        self.strategy = strategy or CachingStrategy()
        self._card_infos = self._get_manager(CardInfo, upstream.iter_card_infos)
        self._game_characters = self._get_manager(GameCharacter, upstream.iter_game_characters)
        self._extra_characters = self._get_manager(ExtraCharacter, upstream.iter_extra_characters)
        self._music_infos = self._get_manager(MusicInfo, upstream.iter_music_infos)
        self._music_versions = self._get_manager(MusicVersion, upstream.iter_music_versions)
        self._live_infos = self._get_manager(LiveInfo, upstream.iter_live_infos)

    def _models_path(self, typ: type[AnyIdModel]) -> Path:
        return self.path / typ.__name__

    def _get_manager(
        self, typ: type[AnyIdModel], updater: _Updater[AnyIdModel]
    ) -> _CacheManager[AnyIdModel]:
        return _CacheManager[AnyIdModel](self._models_path(typ), typ, self.strategy, updater)

    def iter_card_infos(self) -> AsyncIterable[CardInfo]:
        return self._card_infos.iter()

    async def get_card_info(self, id: int) -> CardInfo:
        return await self._card_infos.get(id)

    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        raise NotImplementedError

    def iter_game_characters(self) -> AsyncIterable[GameCharacter]:
        return self._game_characters.iter()

    async def get_game_character(self, id: int) -> GameCharacter:
        return await self._game_characters.get(id)

    def iter_extra_characters(self) -> AsyncIterable[ExtraCharacter]:
        return self._extra_characters.iter()

    async def get_extra_character(self, id: int) -> ExtraCharacter:
        return await self._extra_characters.get(id)

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
        return self._music_infos.iter()

    async def get_music_info(self, id: int) -> MusicInfo:
        return await self._music_infos.get(id)

    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        raise NotImplementedError

    def iter_music_versions(self) -> AsyncIterable[MusicVersion]:
        return self._music_versions.iter()

    async def get_music_version(self, id: int) -> MusicVersion:
        return await self._music_versions.get(id)

    async def iter_versions_of_music(self, id: int) -> AsyncIterable[MusicVersion]:
        async for version in self.iter_music_versions():
            if version.music_id == id:
                yield version

    def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        return self._live_infos.iter()

    async def get_live_info(self, id: int) -> LiveInfo:
        return await self._live_infos.get(id)

    async def iter_live_infos_of_music(self, id: int) -> AsyncIterable[LiveInfo]:
        async for info in self.iter_live_infos():
            if info.music_id == id:
                yield info
