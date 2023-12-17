import abc
from typing import AsyncIterable

from sekai.core.models.card import CardInfo, Deck
from sekai.core.models.chara import Character
from sekai.core.models.live import LiveInfo
from sekai.core.models.music import MusicInfo, MusicVersion
from sekai.core.models.user import Achievement, UserInfo


class UserApi(abc.ABC):
    @abc.abstractmethod
    async def get_user_info(self, id: int) -> UserInfo:
        ...

    @abc.abstractmethod
    async def get_user_main_deck(self, id: int) -> Deck:
        ...

    @abc.abstractmethod
    async def get_user_achievement(self, id: int) -> Achievement:
        ...


class MasterApi(abc.ABC):
    @abc.abstractmethod
    def iter_card_infos(self) -> AsyncIterable[CardInfo]:
        ...

    @abc.abstractmethod
    async def get_card_info(self, id: int) -> CardInfo:
        ...

    @abc.abstractmethod
    def search_card_info_by_title(self, keywords: str) -> AsyncIterable[CardInfo]:
        ...

    @abc.abstractmethod
    def iter_characters(self) -> AsyncIterable[Character]:
        ...

    @abc.abstractmethod
    async def get_character(self, id: int) -> Character:
        ...

    @abc.abstractmethod
    def search_character_by_title(self, keywords: str) -> AsyncIterable[Character]:
        ...

    @abc.abstractmethod
    def iter_music_infos(self) -> AsyncIterable[MusicInfo]:
        ...

    @abc.abstractmethod
    async def get_music_info(self, id: int) -> MusicInfo:
        ...

    @abc.abstractmethod
    def search_music_info_by_title(self, keywords: str) -> AsyncIterable[MusicInfo]:
        ...

    @abc.abstractmethod
    def iter_music_versions(self) -> AsyncIterable[MusicVersion]:
        ...

    @abc.abstractmethod
    async def get_music_version(self, id: int) -> MusicVersion:
        ...

    @abc.abstractmethod
    async def get_versions_of_music(self, id: int) -> list[MusicVersion]:
        ...

    @abc.abstractmethod
    def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        ...

    @abc.abstractmethod
    async def get_live_info(self, id: int) -> LiveInfo:
        ...

    @abc.abstractmethod
    async def get_live_infos_of_music(self, id: int) -> list[LiveInfo]:
        ...
