from aiohttp import ClientSession
from async_lru import alru_cache

from sekai.api import context
from sekai.api.exc import ObjectNotFound
from sekai.core.models.card import CardInfo
from sekai.core.models.chara import Character as SharedCharacter
from sekai.core.models.live import DifficultyLevels
from sekai.core.models.music import MusicInfo, MusicVersion

from ._models import BaseResponse, T_Model
from ._models.card import Card
from ._models.chara import Character
from ._models.music import Music, MusicDifficulty, MusicVocal

DEFAULT_API = "https://api.pjsek.ai"


class PjsekaiApi:
    _api: str

    def __init__(self, api: str | None = None) -> None:
        self._api = api or DEFAULT_API

    @property
    def session(self) -> ClientSession:
        return ClientSession(self._api)

    @staticmethod
    def _check_response(response: BaseResponse[T_Model]) -> BaseResponse[T_Model]:
        if not response.data:
            raise ObjectNotFound
        return response

    @alru_cache(ttl=context.cache_ttl)
    async def get_card_info(self, id: int) -> CardInfo:
        async with self.session as session:
            async with session.get("/database/master/cards", params={"id": id}) as response:
                data = await response.read()
                query = self._check_response(BaseResponse[Card].model_validate_json(data))
                return query.data[0].to_shared_model()

    @alru_cache(ttl=context.cache_ttl)
    async def get_character(self, id: int) -> SharedCharacter:
        async with self.session as session:
            async with session.get(
                "/database/master/gameCharacters", params={"id": id}
            ) as response:
                data = await response.read()
                query = self._check_response(BaseResponse[Character].model_validate_json(data))
                return query.data[0].to_shared_model()

    @alru_cache(ttl=context.cache_ttl)
    async def get_music_info(self, id: int) -> MusicInfo:
        async with self.session as session:
            async with session.get("/database/master/musics", params={"id": id}) as response:
                data = await response.read()
                query = self._check_response(BaseResponse[Music].model_validate_json(data))
                return query.data[0].to_shared_model()

    @alru_cache(ttl=context.cache_ttl)
    async def get_music_version(self, id: int) -> MusicVersion:
        async with self.session as session:
            async with session.get("/database/master/musicVocals", params={"id": id}) as response:
                data = await response.read()
                query = self._check_response(BaseResponse[MusicVocal].model_validate_json(data))
                return query.data[0].to_shared_model()

    @alru_cache(ttl=context.cache_ttl)
    async def get_music_versions(self, id: int) -> list[MusicVersion]:
        async with self.session as session:
            async with session.get(
                "/database/master/musicVocals", params={"musicId": id}
            ) as response:
                data = await response.read()
                query = self._check_response(BaseResponse[MusicVocal].model_validate_json(data))
                return [vocal.to_shared_model() for vocal in query.data]

    @alru_cache(ttl=context.cache_ttl)
    async def get_music_difficulty_levels(self, id: int) -> DifficultyLevels:
        async with self.session as session:
            async with session.get(
                "/database/master/musicDifficulties", params={"musicId": id}
            ) as response:
                data = await response.read()
                query = self._check_response(
                    BaseResponse[MusicDifficulty].model_validate_json(data)
                )
                return dict(vocal.to_difficulty_level_tuple() for vocal in query.data)
