import abc
from typing import Any, Generic, Literal, TypeVar

from aiogram import Bot
from aiogram.filters.callback_data import CallbackData, CallbackQueryFilter
from aiogram.filters.command import Command, CommandObject, CommandPatternType
from aiogram.types import CallbackQuery, Message
from typing_extensions import Self


class Event(abc.ABC, CallbackData, prefix=""):
    @classmethod
    @abc.abstractmethod
    def from_command(cls, command: CommandObject) -> Self:
        ...


_T_Event = TypeVar("_T_Event", bound=Event)


class EventCommand(Command, Generic[_T_Event]):
    event: type[_T_Event]

    def __init__(
        self,
        *values: CommandPatternType,  # type: ignore
        event: type[_T_Event],
        **kwargs: Any,
    ):
        self.event = event
        super().__init__(*values, **kwargs)

    async def __call__(self, update: Message, bot: Bot) -> bool | dict[str, Any]:
        result = await super().__call__(update, bot)
        if isinstance(result, bool):
            return result
        try:
            data = self.event.from_command(result.pop("command"))
        except (TypeError, ValueError):
            return False
        result["event"] = data
        return result


class EventCallbackQuery(CallbackQueryFilter, Generic[_T_Event]):
    event: type[_T_Event]

    def __init__(
        self,
        event: type[_T_Event],
    ):
        self.event = event
        super().__init__(callback_data=event)

    async def __call__(self, update: CallbackQuery) -> Literal[False] | dict[str, Any]:
        result = await super().__call__(update)
        if result is False:
            return result
        result["event"] = result.pop("callback_data")
        return result
