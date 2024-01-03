import abc
from dataclasses import dataclass
from enum import IntEnum, auto


class CardPattern(IntEnum):
    NORMAL = auto()
    SPECIAL_TRAINED = auto()


@dataclass(frozen=True)
class Asset:
    data: bytes
    extension: str

    def __post_init__(self) -> None:
        assert self.extension.startswith("."), "extension should starts with '.'."


class AssetProvider(abc.ABC):
    @abc.abstractmethod
    async def get_card_banner(self, id: str, pattern: CardPattern) -> Asset:
        ...

    @abc.abstractmethod
    async def get_card_cutout(self, id: str, pattern: CardPattern) -> Asset:
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
