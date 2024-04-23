from datetime import datetime
from enum import IntEnum, auto

from sekai.core.models import SharedModel


class CardRarity(IntEnum):
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    BIRTHDAY = auto()


class Card(SharedModel):
    id: int
    level: int
    master_rank: int
    special_trained: bool


class TotalPower(SharedModel):
    area_item_bonus: int
    basic_card_total_power: int
    character_rank_bonus: int
    honor_bonus: int
    total_power: int


class Deck(SharedModel):
    id: int
    name: str
    leader: Card
    subleader: Card
    members: tuple[Card, Card, Card, Card, Card]
    total_power: TotalPower


class CardInfo(SharedModel):
    id: int
    title: str
    character: int
    rarity: CardRarity
    asset_id: str
    released: datetime
    can_special_train: bool
