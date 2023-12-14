from datetime import datetime

from sekai.core.models import ToSharedModel
from sekai.core.models.card import CardInfo, CardRarity

from . import BaseSchema

_RARITY = {
    "rarity_1": CardRarity.ONE,
    "rarity_2": CardRarity.TWO,
    "rarity_3": CardRarity.THREE,
    "rarity_4": CardRarity.FOUR,
    "rarity_birthday": CardRarity.BIRTHDAY,
}


class CardParameter(BaseSchema):
    id: int
    card_id: int
    card_level: int
    card_parameter_type: str
    power: int


class Card(BaseSchema, ToSharedModel[CardInfo]):
    id: int
    seq: int
    character_id: int
    card_rarity_type: str
    special_training_power_1_bonus_fixed: int
    special_training_power_2_bonus_fixed: int
    special_training_power_3_bonus_fixed: int
    attr: str
    support_unit: str
    skill_id: int
    card_skill_name: str
    prefix: str
    assetbundle_name: str
    gacha_phrase: str
    flavor_text: str
    release_at: int
    archive_published_at: int
    card_parameters: list[CardParameter]

    def to_shared_model(self) -> CardInfo:
        return CardInfo(
            id=self.id,
            title=self.prefix,
            character=self.character_id,
            rarity=_RARITY[self.card_rarity_type],
            asset_id=self.assetbundle_name,
            release=datetime.utcfromtimestamp(self.release_at / 1000),
        )
