from enum import IntEnum, auto

from sekai.core.models import SharedModel


class Gender(IntEnum):
    MALE = auto()
    FEMALE = auto()
    SECRET = auto()


class Name(SharedModel):
    first_name: str | None = None
    given_name: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''}{self.given_name}"

    def __str__(self) -> str:
        return self.full_name


class Character(SharedModel):
    id: int
    name: Name
    gender: Gender
    height: int
