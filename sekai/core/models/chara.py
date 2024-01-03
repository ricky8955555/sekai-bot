from enum import IntEnum, auto

from sekai.core.models import SharedModel


class Gender(IntEnum):
    MALE = auto()
    FEMALE = auto()
    SECRET = auto()


class CharacterType(IntEnum):
    GAME = auto()
    EXTRA = auto()


class Name(SharedModel):
    first_name: str
    last_name: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name}{self.last_name or ''}"

    def __str__(self) -> str:
        return self.full_name


class CharacterInfo(SharedModel):
    id: int
    name: Name


class GameCharacter(CharacterInfo):
    gender: Gender
    height: int


class ExtraCharacter(CharacterInfo):
    pass


class Character(SharedModel):
    id: int
    type: CharacterType
