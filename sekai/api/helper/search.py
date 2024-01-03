from enum import IntEnum, auto
from typing import AsyncIterable, Callable, TypeVar

from sekai.api import MasterApi
from sekai.core.models import T_Model
from sekai.core.models.card import CardInfo
from sekai.core.models.music import MusicInfo

_T_MasterApi = TypeVar("_T_MasterApi", bound=MasterApi)


class MatchMethod(IntEnum):
    FULL_MATCH = auto()
    PART_FULL_MATCH = auto()
    PART_PARTIAL_MATCH = auto()


DEFAULT_METHOD = MatchMethod.FULL_MATCH


def make_master_api_search_helper(base: type[_T_MasterApi]):
    class MasterApiSearchHelper(base):
        @staticmethod
        def match(keywords: str, data: list[str], method: MatchMethod) -> bool:
            match method:
                case MatchMethod.FULL_MATCH:
                    return not set(data).difference(keywords.split())
                case MatchMethod.PART_FULL_MATCH:
                    return bool(set(data).intersection(keywords.split()))
                case MatchMethod.PART_PARTIAL_MATCH:
                    return all(
                        any(keyword in part for part in data) for keyword in keywords.split()
                    )

        @staticmethod
        async def _search(
            iterator: AsyncIterable[T_Model],
            keywords: str,
            data: Callable[[T_Model], list[str]],
            method: MatchMethod,
        ) -> AsyncIterable[T_Model]:
            async for model in iterator:
                if MasterApiSearchHelper.match(keywords, data(model), method):
                    yield model

        def search_music_info_by_title(
            self, keywords: str, method: MatchMethod = DEFAULT_METHOD
        ) -> AsyncIterable[MusicInfo]:
            return self._search(
                super().iter_music_infos(), keywords, lambda model: [model.title], method
            )

        def search_music_info_by_artist(
            self, keywords: str, method: MatchMethod = DEFAULT_METHOD
        ) -> AsyncIterable[MusicInfo]:
            return self._search(
                super().iter_music_infos(),
                keywords,
                # priority: composer > lyricist > arranger
                lambda model: [model.composer, model.lyricist, model.arranger],
                method,
            )

        def search_card_info_by_title(
            self, keywords: str, method: MatchMethod = DEFAULT_METHOD
        ) -> AsyncIterable[CardInfo]:
            return self._search(
                super().iter_card_infos(), keywords, lambda model: [model.title], method
            )

    return MasterApiSearchHelper
