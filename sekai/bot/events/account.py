from aiogram.filters.command import CommandObject

from sekai.bot.events import Event


class AccountBindEvent(Event, prefix="bind"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "AccountBindEvent":
        if not command.args:
            raise ValueError
        return AccountBindEvent(id=int(command.args.strip()))
