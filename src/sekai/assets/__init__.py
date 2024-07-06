import abc
from enum import IntEnum, auto


class CardPattern(IntEnum):
    NORMAL = auto()
    SPECIAL_TRAINED = auto()


class AssetProvider(abc.ABC):
    @abc.abstractmethod
    async def get_card_banner(self, id: str, pattern: CardPattern) -> bytes:
        ...

    @abc.abstractmethod
    async def get_card_cutout(self, id: str, pattern: CardPattern) -> bytes:
        ...

    @abc.abstractmethod
    async def get_music(self, id: str) -> bytes:
        ...

    @abc.abstractmethod
    async def get_music_preview(self, id: str) -> bytes:
        ...

    @abc.abstractmethod
    async def get_music_cover(self, id: str) -> bytes:
        ...

    @abc.abstractmethod
    async def get_gacha_logo(self, id: str) -> bytes:
        ...
