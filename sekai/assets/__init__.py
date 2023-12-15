import abc
from dataclasses import dataclass
from enum import IntEnum, auto


class CardBannerType(IntEnum):
    NORMAL = auto()
    SPECIAL_TRAINED = auto()


@dataclass
class Asset:
    data: bytes
    extension: str


class AssetProvider(abc.ABC):
    @abc.abstractmethod
    async def get_card_banner(self, id: str, type: CardBannerType) -> Asset:
        ...

    @abc.abstractmethod
    async def get_card_cutout(self, id: str) -> Asset:
        ...

    @abc.abstractmethod
    async def get_music(self, id: str) -> Asset:
        ...

    @abc.abstractmethod
    async def get_music_preview(self, id: str) -> Asset:
        ...

    @abc.abstractmethod
    async def get_music_cover(self, id: str) -> Asset:
        ...
