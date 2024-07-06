import contextlib

from aiohttp import ClientResponse, ClientSession

from sekai.assets import AssetProvider, CardPattern
from sekai.assets.exc import AssetNotFound

DEFAULT_SERVER = "https://assets.pjsek.ai"


class PjsekaiAssets(AssetProvider):
    _server: str

    @property
    def session(self) -> ClientSession:
        return ClientSession(self._server)

    def __init__(self, server: str | None = None) -> None:
        self._server = server or DEFAULT_SERVER

    @staticmethod
    def _check_response(response: ClientResponse) -> ClientResponse:
        if not response.ok:
            raise AssetNotFound
        return response

    async def _fetch_asset(self, path: str) -> bytes:
        async with self.session as session:
            async with session.get(path) as response:
                response = self._check_response(response)
                return await response.read()

    async def get_card_banner(self, id: str, pattern: CardPattern) -> bytes:
        path = f"/file/pjsekai-assets/startapp/character/member/{id}/"
        match pattern:
            case CardPattern.NORMAL:
                path += "card_normal.png"
            case CardPattern.SPECIAL_TRAINED:
                path += "card_after_training.png"
        return await self._fetch_asset(path)

    async def get_card_cutout(self, id: str, pattern: CardPattern) -> bytes:
        path = f"/file/pjsekai-assets/startapp/character/member_cutout/{id}/"
        match pattern:
            case CardPattern.NORMAL:
                path += "normal/normal.png"
            case CardPattern.SPECIAL_TRAINED:
                path += "after_training/after_training.png"
        return await self._fetch_asset(path)

    async def get_music(self, id: str) -> bytes:
        raise NotImplementedError

    async def get_music_preview(self, id: str) -> bytes:
        with contextlib.suppress(AssetNotFound):
            return await self._fetch_asset(
                f"/file/pjsekai-assets/startapp/music/short/{id}/{id}_short.flac"
            )
        with contextlib.suppress(AssetNotFound):
            return await self._fetch_asset(
                f"/file/pjsekai-assets/startapp/music/short/{id}/{id}_short.wav"
            )
        raise AssetNotFound

    async def get_music_cover(self, id: str) -> bytes:
        return await self._fetch_asset(f"/file/pjsekai-assets/startapp/music/jacket/{id}/{id}.png")
