from aiogram.filters.command import CommandObject

from sekai.bot.cmpnt import Event


class DeckEvent(Event, prefix="deck"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "DeckEvent":
        if not command.args:
            raise ValueError
        return DeckEvent(id=int(command.args.strip()))


class CardEvent(Event, prefix="card"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "CardEvent":
        if not command.args:
            raise ValueError
        return CardEvent(id=int(command.args.strip()))
