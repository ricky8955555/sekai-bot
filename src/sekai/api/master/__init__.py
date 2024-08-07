import abc
from typing import AsyncIterable

from sekai.core.models.card import CardInfo
from sekai.core.models.chara import Character, CharacterInfo, ExtraCharacter, GameCharacter
from sekai.core.models.gacha import Gacha
from sekai.core.models.live import LiveInfo
from sekai.core.models.music import MusicInfo, MusicVersion
from sekai.core.models.system import SystemInfo


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
    def iter_game_characters(self) -> AsyncIterable[GameCharacter]:
        ...

    @abc.abstractmethod
    async def get_game_character(self, id: int) -> GameCharacter:
        ...

    @abc.abstractmethod
    def iter_extra_characters(self) -> AsyncIterable[ExtraCharacter]:
        ...

    @abc.abstractmethod
    async def get_extra_character(self, id: int) -> ExtraCharacter:
        ...

    @abc.abstractmethod
    def iter_character_infos(self) -> AsyncIterable[CharacterInfo]:
        ...

    @abc.abstractmethod
    async def get_character_info(self, character: Character) -> CharacterInfo:
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
    def iter_versions_of_music(self, id: int) -> AsyncIterable[MusicVersion]:
        ...

    @abc.abstractmethod
    def iter_live_infos(self) -> AsyncIterable[LiveInfo]:
        ...

    @abc.abstractmethod
    async def get_live_info(self, id: int) -> LiveInfo:
        ...

    @abc.abstractmethod
    def iter_live_infos_of_music(self, id: int) -> AsyncIterable[LiveInfo]:
        ...

    @abc.abstractmethod
    async def get_current_system_info(self) -> SystemInfo:
        ...

    @abc.abstractmethod
    def iter_gachas(self) -> AsyncIterable[Gacha]:
        ...

    @abc.abstractmethod
    async def get_gacha(self, id: int) -> Gacha:
        ...

    @abc.abstractmethod
    def search_gacha_by_name(self, keywords: str) -> AsyncIterable[Gacha]:
        ...
