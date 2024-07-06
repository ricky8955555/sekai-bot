import abc

from sekai.core.models.card import Deck
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
