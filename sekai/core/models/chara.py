from enum import IntEnum, auto

from sekai.core.models import SharedModel


class Gender(IntEnum):
    MALE = auto()
    FEMALE = auto()
    SECRET = auto()


class CharacterType(IntEnum):
    GAME = auto()
    EXTRA = auto()


class CharacterInfo(SharedModel):
    id: int
    name: str


class GameCharacter(CharacterInfo):
    gender: Gender
    height: int


class ExtraCharacter(CharacterInfo):
    pass


class Character(SharedModel):
    id: int
    type: CharacterType
