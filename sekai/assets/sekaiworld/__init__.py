from aiohttp import ClientResponse, ClientSession

from sekai.assets import Asset, AssetProvider, CardPattern
from sekai.assets.exc import AssetNotFound

DEFAULT_SERVER = "https://storage.sekai.best"


class SekaiWorldAssets(AssetProvider):
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

    async def get_card_banner(self, id: str, pattern: CardPattern) -> Asset:
        path = f"/sekai-assets/character/member/{id}_rip/"
        match pattern:
            case CardPattern.NORMAL:
                path += "card_normal.png"
            case CardPattern.SPECIAL_TRAINED:
                path += "card_after_training.png"
        return Asset(await self._fetch_asset(path), ".png")

    async def get_card_cutout(self, id: str, pattern: CardPattern) -> Asset:
        path = f"/sekai-assets/character/member_cutout/{id}_rip/"
        match pattern:
            case CardPattern.NORMAL:
                path += "normal.png"
            case CardPattern.SPECIAL_TRAINED:
                path += "after_training.png"
        return Asset(await self._fetch_asset(path), ".png")

    async def get_music(self, id: str) -> Asset:
        return Asset(
            await self._fetch_asset(f"/sekai-assets/music/long/{id}_rip/{id}.mp3"),
            ".mp3",
        )

    async def get_music_preview(self, id: str) -> Asset:
        return Asset(
            await self._fetch_asset(f"/sekai-assets/music/short/{id}_rip/{id}_short.mp3"),
            ".mp3",
        )

    async def get_music_cover(self, id: str) -> Asset:
        return Asset(
            await self._fetch_asset(f"/sekai-assets/music/jacket/{id}_rip/{id}.png"),
            ".png",
        )
