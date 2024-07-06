from enum import IntEnum, auto

from sekai.core.models import SharedModel


class LiveDifficulty(IntEnum):
    EASY = auto()
    NORMAL = auto()
    HARD = auto()
    EXPERT = auto()
    MASTER = auto()
    APPEND = auto()


class LiveInfo(SharedModel):
    id: int
    music_id: int
    difficulty: LiveDifficulty
    level: int
