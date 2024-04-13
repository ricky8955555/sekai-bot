import asyncio
import logging
import shutil
from asyncio import Event
from dataclasses import dataclass
from datetime import timedelta
from packaging.version import Version
from pathlib import Path
from typing import AsyncIterable, Awaitable, Callable, Protocol, TypeVar

from aiofile import async_open
from pydantic import RootModel
from tenacity import before_sleep_log, retry, wait_fixed

from sekai.api.exc import ObjectNotFound
from sekai.api.master import MasterApi
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
from sekai.core.models.system import SystemInfo


logger = logging.getLogger(__name__)


class IdModel(Protocol):
    id: int


AnyIdModel = TypeVar("AnyIdModel", bound=IdModel)


@dataclass(frozen=True)
class CachingStrategy:
    check_cycle: timedelta = timedelta(hours=1)


class CachingMasterApi(MasterApi):
    path: Path
    strategy: CachingStrategy
    _updating: Event
    _upstreams: dict[type[IdModel], Callable[[], AsyncIterable[IdModel]]]
    _upstream_system_info: Callable[[], Awaitable[SystemInfo]]
    _cache_task: asyncio.Task[None] | None

    def __init__(
        self, upstream: MasterApi, cache_path: Path, strategy: CachingStrategy | None = None
    ) -> None:
        self.upstream = upstream
        self.path = cache_path
        self.strategy = strategy or CachingStrategy()
        self._updating = Event()
        self._upstreams = {
            CardInfo: upstream.iter_card_infos,
            GameCharacter: upstream.iter_game_characters,
            ExtraCharacter: upstream.iter_extra_characters,
            LiveInfo: upstream.iter_live_infos,
            MusicInfo: upstream.iter_music_infos,
            MusicVersion: upstream.iter_music_versions,
        }
        self._upstream_system_info = upstream.get_current_system_info
        self._updating.set()
        self._cache_task = None

    @property
    def _cached_system_info_path(self) -> Path:
        return self.path / ".cache"

    def _models_path(self, typ: type[AnyIdModel]) -> Path:
        return self.path / typ.__name__

    def _cache_path(self, typ: type[AnyIdModel], id: int) -> Path:
        return (self._models_path(typ) / str(id)).with_suffix(".json")

    def run_cache_task(self) -> None:
        assert self._cache_task is None, "another cache task is running."
        self._cache_task = asyncio.create_task(self._cache_worker())

    def cancel_cache_task(self) -> None:
        assert self._cache_task is not None, "no cache task is running."
        self._cache_task.cancel()
        self._cache_task = None

    async def get_current_system_info(self) -> SystemInfo:
        if not self._cached_system_info_path.exists():
            raise ObjectNotFound
        async with async_open(self._cached_system_info_path, "r") as afp:
            data = await afp.read()
        return SystemInfo.model_validate_json(data)

    async def _update_system_info(self, info: SystemInfo) -> None:
        data = info.model_dump_json()
        async with async_open(self._cached_system_info_path, "w") as afp:
            await afp.write(data)

    async def _cache_worker(self) -> None:
        while True:
            await self._check_and_update_cache()
            await asyncio.sleep(self.strategy.check_cycle.total_seconds())

    @retry(wait=wait_fixed(5), before_sleep=before_sleep_log(logger, logging.WARNING, True))
    async def _check_and_update_cache(self) -> None:
        if not self._updating.is_set():
            return
        if self._cached_system_info_path.exists():
            upstream = await self._upstream_system_info()
            cached = await self.get_current_system_info()
            if Version(cached.asset_version) >= Version(upstream.asset_version):
                return
        await self.update_cache()

    async def update_cache(self) -> None:
        async def updater(
            typ: type[IdModel], provider: Callable[[], AsyncIterable[IdModel]]
        ) -> None:
            async for model in provider():
                path = self._cache_path(typ, model.id)
                wrapped = RootModel(root=model)
                data = wrapped.model_dump_json()
                async with async_open(path, "w") as afp:
                    await afp.write(data)

        assert self._updating.is_set(), "cache is updating."
        self._updating.clear()
        try:
            upstream = await self._upstream_system_info()
            self._rebuild_cache_tree()
            updaters = [updater(typ, provider) for (typ, provider) in self._upstreams.items()]
            await asyncio.gather(*updaters)
            await self._update_system_info(upstream)
        finally:
            self._updating.set()

    def _rebuild_cache_tree(self) -> None:
        shutil.rmtree(self.path)
        self.path.mkdir()
        for typ in self._upstreams.keys():
            self._models_path(typ).mkdir()

    async def _get_cache(self, typ: type[AnyIdModel], id: int) -> AnyIdModel:
        await self._updating.wait()
        path = self._cache_path(typ, id)
        if not path.exists():
            raise ObjectNotFound
        assert path.is_file(), f"{path} is not a file."
        async with async_open(path, "r") as afp:
            data = await afp.read()
        wrapped_type = RootModel.__class_getitem__(typ)
        cache = wrapped_type.model_validate_json(data)  # type: ignore
        return cache.root  # type: ignore

    async def _iter_caches(self, typ: type[AnyIdModel]) -> AsyncIterable[AnyIdModel]:
        await self._updating.wait()
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

    def iter_card_infos(self) -> AsyncIterable[CardInfo]:
        return self._iter_caches(CardInfo)

    async def get_card_info(self, id: int) -> CardInfo:
        return await self._get_cache(CardInfo, id)

    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        raise NotImplementedError

    def iter_game_characters(self) -> AsyncIterable[GameCharacter]:
        return self._iter_caches(GameCharacter)

    async def get_game_character(self, id: int) -> GameCharacter:
        return await self._get_cache(GameCharacter, id)

    def iter_extra_characters(self) -> AsyncIterable[ExtraCharacter]:
        return self._iter_caches(ExtraCharacter)

    async def get_extra_character(self, id: int) -> ExtraCharacter:
        return await self._get_cache(ExtraCharacter, id)

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
        return self._iter_caches(MusicInfo)

    async def get_music_info(self, id: int) -> MusicInfo:
        return await self._get_cache(MusicInfo, id)

    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        raise NotImplementedError

    def iter_music_versions(self) -> AsyncIterable[MusicVersion]:
        return self._iter_caches(MusicVersion)

    async def get_music_version(self, id: int) -> MusicVersion:
        return await self._get_cache(MusicVersion, id)

    async def iter_versions_of_music(self, id: int) -> AsyncIterable[MusicVersion]:
        async for version in self.iter_music_versions():
            if version.music_id == id:
                yield version

    def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        return self._iter_caches(LiveInfo)

    async def get_live_info(self, id: int) -> LiveInfo:
        return await self._get_cache(LiveInfo, id)

    async def iter_live_infos_of_music(self, id: int) -> AsyncIterable[LiveInfo]:
        async for info in self.iter_live_infos():
            if info.music_id == id:
                yield info
