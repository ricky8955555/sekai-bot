from datetime import datetime

from sekai.core.models import ToSharedModel
from sekai.core.models.card import CardAttribute, CardInfo, CardRarity

from . import TIMEZONE, BaseSchema

RARITY = {
    "rarity_1": CardRarity.ONE,
    "rarity_2": CardRarity.TWO,
    "rarity_3": CardRarity.THREE,
    "rarity_4": CardRarity.FOUR,
    "rarity_birthday": CardRarity.BIRTHDAY,
}


ATTRIBUTE = {
    "cool": CardAttribute.COOL,
    "cute": CardAttribute.CUTE,
    "happy": CardAttribute.HAPPY,
    "mysterious": CardAttribute.MYSTERIOUS,
    "pure": CardAttribute.PURE
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
            rarity=RARITY[self.card_rarity_type],
            attribute=ATTRIBUTE[self.attr],
            asset_id=self.assetbundle_name,
            released=datetime.fromtimestamp(self.release_at / 1000, TIMEZONE),
            can_special_train=any(
                [
                    self.special_training_power_1_bonus_fixed,
                    self.special_training_power_2_bonus_fixed,
                    self.special_training_power_3_bonus_fixed,
                ]
            ),
        )
