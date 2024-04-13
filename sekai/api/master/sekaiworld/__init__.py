from typing import AsyncIterable, cast

from aiohttp import ClientSession
from pydantic import RootModel

from sekai.api.exc import ObjectNotFound
from sekai.api.master import MasterApi
from sekai.core.models.card import CardInfo
from sekai.core.models.chara import Character, CharacterInfo, CharacterType, ExtraCharacter
from sekai.core.models.chara import GameCharacter as SharedGameCharacter
from sekai.core.models.live import LiveInfo
from sekai.core.models.music import MusicInfo, MusicVersion
from sekai.core.models.system import SystemInfo as SharedSystemInfo

from .._models import AnyModel
from .._models.card import Card
from .._models.chara import GameCharacter, OutsideCharacter
from .._models.music import Music, MusicDifficulty, MusicVocal
from .._models.system import SystemInfo

DEFAULT_API = "https://sekai-world.github.io"


class SekaiWorldApi(MasterApi):
    _api: str

    def __init__(self, api: str | None = None) -> None:
        self._api = api or DEFAULT_API

    @property
    def session(self) -> ClientSession:
        return ClientSession(self._api)

    async def _iter(self, path: str, type: type[AnyModel]) -> list[AnyModel]:
        async with self.session as session:
            async with session.get(path) as response:
                resp_type = cast(
                    RootModel[list[AnyModel]], RootModel[list[AnyModel]].__class_getitem__(type)
                )
                json = await response.read()
                data = resp_type.model_validate_json(json)
                return data.root

    async def _get(self, path: str, type: type[AnyModel]) -> AnyModel:
        async with self.session as session:
            async with session.get(path) as response:
                resp_type = cast(RootModel[AnyModel], RootModel.__class_getitem__(type))
                json = await response.read()
                data = resp_type.model_validate_json(json)
                return data.root

    async def iter_card_infos(self) -> AsyncIterable[CardInfo]:
        for model in await self._iter("/sekai-master-db-diff/cards.json", Card):
            yield model.to_shared_model()

    async def get_card_info(self, id: int) -> CardInfo:
        async for model in self.iter_card_infos():
            if model.id == id:
                return model
        raise ObjectNotFound

    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        raise NotImplementedError

    async def iter_game_characters(self) -> AsyncIterable[SharedGameCharacter]:
        for model in await self._iter("/sekai-master-db-diff/gameCharacters.json", GameCharacter):
            yield model.to_shared_model()

    async def get_game_character(self, id: int) -> SharedGameCharacter:
        async for model in self.iter_game_characters():
            if model.id == id:
                return model
        raise ObjectNotFound

    async def iter_extra_characters(self) -> AsyncIterable[ExtraCharacter]:
        for model in await self._iter(
            "/sekai-master-db-diff/outsideCharacters.json", OutsideCharacter
        ):
            yield model.to_shared_model()

    async def get_extra_character(self, id: int) -> ExtraCharacter:
        async for model in self.iter_extra_characters():
            if model.id == id:
                return model
        raise ObjectNotFound

    async def get_character_info(self, character: Character) -> CharacterInfo:
        match character.type:
            case CharacterType.GAME:
                return await self.get_game_character(character.id)
            case CharacterType.EXTRA:
                return await self.get_extra_character(character.id)

    async def iter_character_infos(self) -> AsyncIterable[CharacterInfo]:
        async for model in self.iter_game_characters():
            yield model
        async for model in self.iter_extra_characters():
            yield model

    async def iter_music_infos(self) -> AsyncIterable[MusicInfo]:
        for model in await self._iter("/sekai-master-db-diff/musics.json", Music):
            yield model.to_shared_model()

    async def get_music_info(self, id: int) -> MusicInfo:
        async for model in self.iter_music_infos():
            if model.id == id:
                return model
        raise ObjectNotFound

    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        raise NotImplementedError

    async def iter_music_versions(self) -> AsyncIterable[MusicVersion]:
        for model in await self._iter("/sekai-master-db-diff/musicVocals.json", MusicVocal):
            yield model.to_shared_model()

    async def get_music_version(self, id: int) -> MusicVersion:
        async for model in self.iter_music_versions():
            if model.id == id:
                return model
        raise ObjectNotFound

    async def iter_versions_of_music(self, id: int) -> AsyncIterable[MusicVersion]:
        async for model in self.iter_music_versions():
            if model.music_id == id:
                yield model
        raise ObjectNotFound

    async def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        for model in await self._iter(
            "/sekai-master-db-diff/musicDifficulties.json", MusicDifficulty
        ):
            yield model.to_shared_model()

    async def get_live_info(self, id: int) -> LiveInfo:
        async for model in self.iter_live_infos():
            if model.id == id:
                return model
        raise ObjectNotFound

    async def iter_live_infos_of_music(self, id: int) -> AsyncIterable[LiveInfo]:
        async for model in self.iter_live_infos():
            if model.music_id == id:
                yield model
        raise ObjectNotFound

    async def get_current_system_info(self) -> SharedSystemInfo:
        info = await self._get("/sekai-master-db-diff/versions.json", SystemInfo)
        return info.to_shared_model()
