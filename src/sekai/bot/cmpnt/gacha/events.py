from aiogram.filters.command import CommandObject

from sekai.bot.cmpnt import Event
from sekai.bot.cmpnt.gacha.models import DoGachaType
from sekai.utils import iters


class GachaEvent(Event, prefix="gacha"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "GachaEvent":
        if not command.args:
            raise ValueError
        return GachaEvent(id=int(command.args.strip()))


class DoGachaEvent(Event, prefix="dogacha"):
    id: int
    type: DoGachaType = DoGachaType.NORMAL

    @classmethod
    def from_command(cls, command: CommandObject) -> "DoGachaEvent":
        if not command.args or len(args := command.args.split()) > 2:
            raise ValueError
        type = DoGachaType[type_str.upper()] if (type_str := iters.at(args, 1)) else None
        return DoGachaEvent(
            id=int(args[0].strip()),
            type=type or DoGachaType.NORMAL,
        )
