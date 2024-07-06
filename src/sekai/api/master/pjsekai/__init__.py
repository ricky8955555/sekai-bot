from typing import Any, AsyncIterable, cast

from aiohttp import ClientSession

from sekai.api.exc import ObjectNotFound
from sekai.api.master import MasterApi
from sekai.core.models.card import CardInfo
from sekai.core.models.chara import Character, CharacterInfo, CharacterType, ExtraCharacter
from sekai.core.models.chara import GameCharacter as SharedGameCharacter
from sekai.core.models.gacha import Gacha as SharedGacha
from sekai.core.models.live import LiveInfo
from sekai.core.models.music import MusicInfo, MusicVersion
from sekai.core.models.system import SystemInfo as SharedSystemInfo

from .._models import AnyModel
from .._models.card import Card
from .._models.chara import GameCharacter, OutsideCharacter
from .._models.gacha import Gacha
from .._models.music import Music, MusicDifficulty, MusicVocal
from .._models.system import SystemInfo
from ._models import BaseResponse

DEFAULT_API = "https://api.pjsek.ai"


class PjsekaiApi(MasterApi):
    _api: str

    def __init__(self, api: str | None = None) -> None:
        self._api = api or DEFAULT_API

    @property
    def session(self) -> ClientSession:
        return ClientSession(self._api)

    async def _iter(
        self,
        path: str,
        type: type[AnyModel],
        limit: int = 20,
        skip: int = 0,
        params: dict[str, Any] | None = None,
    ) -> AsyncIterable[AnyModel]:
        params = params or {}
        assert (
            "$limit" not in params and "$skip" not in params
        ), "'$limit' and '$skip' should not be in the params."
        while True:
            async with self.session as session:
                async with session.get(
                    path, params=({"$limit": limit, "$skip": skip} | params)
                ) as response:
                    resp_type = cast(BaseResponse[AnyModel], BaseResponse.__class_getitem__(type))
                    json = await response.read()
                    data = resp_type.model_validate_json(json)
                    for model in data.data:
                        yield model
                    if data.skip + data.limit >= data.total:
                        return
            skip += limit

    async def _get(
        self, path: str, type: type[AnyModel], *args: Any, **kwargs: Any
    ) -> list[AnyModel]:
        async with self.session as session:
            async with session.get(path, *args, **kwargs) as response:
                resp_type = cast(BaseResponse[AnyModel], BaseResponse.__class_getitem__(type))
                json = await response.read()
                data = resp_type.model_validate_json(json)
                if not data.data:
                    raise ObjectNotFound
                return data.data

    async def iter_card_infos(self, limit: int = 20, skip: int = 0) -> AsyncIterable[CardInfo]:
        async for model in self._iter("/database/master/cards", Card, limit, skip):
            yield model.to_shared_model()

    async def get_card_info(self, id: int) -> CardInfo:
        models = await self._get("/database/master/cards", Card, params={"id": id})
        return models[0].to_shared_model()

    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        raise NotImplementedError

    async def iter_game_characters(
        self, limit: int = 20, skip: int = 0
    ) -> AsyncIterable[SharedGameCharacter]:
        async for model in self._iter(
            "/database/master/gameCharacters", GameCharacter, limit, skip
        ):
            yield model.to_shared_model()

    async def get_game_character(self, id: int) -> SharedGameCharacter:
        models = await self._get(
            "/database/master/gameCharacters", GameCharacter, params={"id": id}
        )
        return models[0].to_shared_model()

    async def iter_extra_characters(
        self, limit: int = 20, skip: int = 0
    ) -> AsyncIterable[ExtraCharacter]:
        async for model in self._iter(
            "/database/master/outsideCharacters", OutsideCharacter, limit, skip
        ):
            yield model.to_shared_model()

    async def get_extra_character(self, id: int) -> ExtraCharacter:
        models = await self._get(
            "/database/master/outsideCharacters", OutsideCharacter, params={"id": id}
        )
        return models[0].to_shared_model()

    async def get_character_info(self, character: Character) -> CharacterInfo:
        match character.type:
            case CharacterType.GAME:
                return await self.get_game_character(character.id)
            case CharacterType.EXTRA:
                return await self.get_extra_character(character.id)

    async def iter_character_infos(
        self, limit: int = 20, skip: int = 0
    ) -> AsyncIterable[CharacterInfo]:
        async for model in self.iter_game_characters(limit, skip):
            yield model
        async for model in self.iter_extra_characters(limit, skip):
            yield model

    async def iter_music_infos(self, limit: int = 20, skip: int = 0) -> AsyncIterable[MusicInfo]:
        async for model in self._iter("/database/master/musics", Music, limit, skip):
            yield model.to_shared_model()

    async def get_music_info(self, id: int) -> MusicInfo:
        models = await self._get("/database/master/musics", Music, params={"id": id})
        return models[0].to_shared_model()

    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        raise NotImplementedError

    async def iter_music_versions(
        self, limit: int = 20, skip: int = 0
    ) -> AsyncIterable[MusicVersion]:
        async for model in self._iter("/database/master/musicVocals", MusicVocal, limit, skip):
            yield model.to_shared_model()

    async def get_music_version(self, id: int) -> MusicVersion:
        models = await self._get("/database/master/musicVocals", MusicVocal, params={"id": id})
        return models[0].to_shared_model()

    async def iter_versions_of_music(
        self, id: int, limit: int = 20, skip: int = 0
    ) -> AsyncIterable[MusicVersion]:
        async for vocal in self._iter(
            "/database/master/musicVocals",
            MusicVocal,
            limit,
            skip,
            params={"musicId": id},
        ):
            yield vocal.to_shared_model()

    async def iter_live_infos(self, limit: int = 20, skip: int = 0) -> AsyncIterable[LiveInfo]:
        async for model in self._iter(
            "/database/master/musicDifficulties", MusicDifficulty, limit, skip
        ):
            yield model.to_shared_model()

    async def get_live_info(self, id: int) -> LiveInfo:
        models = await self._get(
            "/database/master/musicDifficulties", MusicDifficulty, params={"id": id}
        )
        return models[0].to_shared_model()

    async def iter_live_infos_of_music(
        self, id: int, limit: int = 20, skip: int = 0
    ) -> AsyncIterable[LiveInfo]:
        async for vocal in self._iter(
            "/database/master/musicDifficulties",
            MusicDifficulty,
            limit,
            skip,
            params={"musicId": id},
        ):
            yield vocal.to_shared_model()

    async def get_current_system_info(self) -> SharedSystemInfo:
        models = await self._get("/system-info", SystemInfo)
        return models[0].to_shared_model()

    async def iter_gachas(self, limit: int = 20, skip: int = 0) -> AsyncIterable[SharedGacha]:
        async for model in self._iter("/database/master/gachas", Gacha, limit, skip):
            yield model.to_shared_model()

    async def get_gacha(self, id: int) -> SharedGacha:
        models = await self._get("/database/master/gachas", Gacha, params={"id": id})
        return models[0].to_shared_model()

    def search_gacha_by_name(self, keywords: str) -> AsyncIterable[SharedGacha]:
        raise NotImplementedError
