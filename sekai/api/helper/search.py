import re
from enum import IntEnum
from typing import AsyncIterable, Callable, TypeVar

from sekai.api import MasterApi
from sekai.core.models import T_Model
from sekai.core.models.card import CardInfo
from sekai.core.models.chara import Character
from sekai.core.models.music import MusicInfo

_T_MasterApi = TypeVar("_T_MasterApi", bound=MasterApi)


class MatchMethod(IntEnum):
    FULL_MATCH = 0
    PARTIAL_MATCH = 1
    SPLIT_FULL_MATCH = 2
    SPLIT_PART_FULL_MATCH = 3
    SPLIT_PART_PARTIAL_MATCH = 4
    REGEX_MATCH = 5


DEFAULT_METHOD = MatchMethod.FULL_MATCH


def make_master_api_search_helper(base: type[_T_MasterApi]):
    class MasterApiSearchHelper(base):
        @staticmethod
        def match(keywords: str, data: str, method: MatchMethod) -> bool:
            match method:
                case MatchMethod.FULL_MATCH:
                    return keywords == data
                case MatchMethod.PARTIAL_MATCH:
                    return keywords in data
                case MatchMethod.SPLIT_FULL_MATCH:
                    return not set(keywords.split()).difference(data.split())
                case MatchMethod.SPLIT_PART_FULL_MATCH:
                    return bool(set(keywords.split()).intersection(data.split()))
                case MatchMethod.SPLIT_PART_PARTIAL_MATCH:
                    keyword_parts = keywords.split()
                    data_parts = data.split()
                    return all(
                        any(keyword in data for data in data_parts) for keyword in keyword_parts
                    )
                case MatchMethod.REGEX_MATCH:
                    return bool(re.match(keywords, data))

        @staticmethod
        async def _search(
            iterator: AsyncIterable[T_Model],
            keywords: str,
            name: Callable[[T_Model], str],
            method: MatchMethod,
        ) -> AsyncIterable[T_Model]:
            async for model in iterator:
                if MasterApiSearchHelper.match(keywords, name(model), method):
                    yield model

        def search_music_info_by_title(
            self, keywords: str, method: MatchMethod = DEFAULT_METHOD
        ) -> AsyncIterable[MusicInfo]:
            return self._search(
                super().iter_music_infos(), keywords, lambda model: model.title, method
            )

        def search_card_info_by_title(
            self, keywords: str, method: MatchMethod = DEFAULT_METHOD
        ) -> AsyncIterable[CardInfo]:
            return self._search(
                super().iter_card_infos(), keywords, lambda model: model.title, method
            )

        def search_character_by_title(
            self, keywords: str, method: MatchMethod = DEFAULT_METHOD
        ) -> AsyncIterable[Character]:
            return self._search(
                super().iter_characters(), keywords, lambda model: model.name.full_name, method
            )

    return MasterApiSearchHelper
