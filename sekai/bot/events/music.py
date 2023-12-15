from enum import IntEnum, auto

from aiogram.filters.command import CommandObject

from sekai.bot.events import Event
from sekai.utils import iters


class MusicEvent(Event, prefix="music"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "MusicEvent":
        if not command.args:
            raise ValueError
        return MusicEvent(id=int(command.args.strip()))


class MusicDownloadType(IntEnum):
    FULL = auto()
    PREVIEW = auto()


class MusicDownloadEvent(Event, prefix="musicdown"):
    id: int
    type: MusicDownloadType = MusicDownloadType.FULL

    @classmethod
    def from_command(cls, command: CommandObject) -> "MusicDownloadEvent":
        if not command.args or len(args := command.args.split()) > 2:
            raise ValueError
        type = MusicDownloadType[type_str.upper()] if (type_str := iters.at(args, 1)) else None
        return MusicDownloadEvent(
            id=int(args[0].strip()),
            type=type or MusicDownloadType.PREVIEW,
        )
