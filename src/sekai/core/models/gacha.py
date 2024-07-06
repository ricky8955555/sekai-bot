from datetime import datetime

from sekai.core.models import SharedModel
from sekai.core.models.card import CardRarity


class GachaCard(SharedModel):
    id: int
    weight: int
    is_pickup: bool
    is_wish: bool


class Gacha(SharedModel):
    id: int
    name: str
    summary: str
    description: str
    asset_id: str
    start: datetime
    end: datetime
    show_period: bool
    rarity_rates: list[tuple[CardRarity, float]]
    card_weights: list[tuple[int, int]]
    pickup_cards: list[int]
    wish_cards: list[int]
