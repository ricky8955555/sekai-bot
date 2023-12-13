import abc
from enum import IntEnum, auto


class CardBannerType(IntEnum):
    NORMAL = auto()
    SPECIAL_TRAINED = auto()


class AssetProvider(abc.ABC):
    @abc.abstractmethod
    async def get_card_banner(self, id: str, type: CardBannerType) -> bytes:
        ...

    @abc.abstractmethod
    async def get_card_cutout(self, id: str) -> bytes:
        ...
