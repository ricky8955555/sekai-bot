from aiohttp import ClientSession
from async_lru import alru_cache

from sekai.api.exc import ObjectNotFound
from sekai.api.user import UserApi
from sekai.core.models.card import Deck
from sekai.core.models.user import Achievement, UserInfo

from ._models.profile import Profile

DEFAULT_API = "https://api.unipjsk.com"

CACHE_TTL = 180


class UnipjskApi(UserApi):
    _api: str

    def __init__(self, api: str | None = None) -> None:
        self._api = api or DEFAULT_API

    @property
    def session(self) -> ClientSession:
        return ClientSession(self._api)

    @staticmethod
    def _check_data(data: bytes) -> bytes:
        if data.strip() == b"{}":
            raise ObjectNotFound
        return data

    @alru_cache(ttl=CACHE_TTL)
    async def _get_profile(self, id: int) -> Profile:
        async with self.session as session:
            async with session.get(f"/api/user/{id}/profile") as response:
                response = response
                data = self._check_data(await response.read())
                profile = Profile.model_validate_json(data)
                return profile

    async def get_user_info(self, id: int) -> UserInfo:
        profile = await self._get_profile(id)
        return profile.to_user_info()

    async def get_user_main_deck(self, id: int) -> Deck:
        profile = await self._get_profile(id)
        return profile.to_deck()

    async def get_user_achievement(self, id: int) -> Achievement:
        profile = await self._get_profile(id)
        return profile.to_achievement()
