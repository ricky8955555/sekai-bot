from aiogram.filters.command import CommandObject

from sekai.bot.cmpnt import Event


class ProfileEvent(Event, prefix="profile"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "ProfileEvent":
        if not command.args:
            raise ValueError
        return ProfileEvent(id=int(command.args.strip()))


class AchievementEvent(Event, prefix="achieve"):
    id: int

    @classmethod
    def from_command(cls, command: CommandObject) -> "AchievementEvent":
        if not command.args:
            raise ValueError
        return AchievementEvent(id=int(command.args.strip()))
