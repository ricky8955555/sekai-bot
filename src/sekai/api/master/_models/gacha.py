from datetime import datetime

from sekai.core.models import ToSharedModel
from sekai.core.models.gacha import Gacha as SharedGacha

from . import TIMEZONE, BaseSchema
from .card import RARITY


class GachaCardRarityRate(BaseSchema):
    id: int
    group_id: int
    card_rarity_type: str
    lottery_type: str
    rate: float


class GachaDetail(BaseSchema):
    id: int
    gacha_id: int
    card_id: int
    weight: int
    is_wish: bool


class GachaBehavior(BaseSchema):
    id: int
    gacha_id: int
    gacha_behavior_type: str
    cost_resource_type: str
    cost_resource_quantity: int
    spin_count: int
    execute_limit: int
    group_id: int
    priority: int
    resource_category: str
    gacha_spinnable_type: str


class GachaPickup(BaseSchema):
    id: int
    gacha_id: int
    card_id: int
    gacha_pickup_type: str


class GachaPickupCostume(BaseSchema):
    pass


class GachaInformation(BaseSchema):
    gacha_id: int
    summary: str
    description: str


class Gacha(BaseSchema, ToSharedModel[SharedGacha]):
    id: int
    gacha_type: str
    name: str
    seq: int
    assetbundle_name: str
    gacha_card_rarity_rate_group_id: int
    start_at: int
    end_at: int
    is_show_period: bool
    wish_select_count: int
    wish_fixed_select_count: int
    wish_limited_select_count: int
    gacha_card_rarity_rates: list[GachaCardRarityRate]
    gacha_details: list[GachaDetail]
    gacha_pickups: list[GachaPickup]
    gacha_pickup_costumes: list[GachaPickupCostume]
    gacha_information: GachaInformation

    def to_shared_model(self) -> SharedGacha:
        return SharedGacha(
            id=self.id,
            name=self.name,
            summary=self.gacha_information.summary,
            description=self.gacha_information.description,
            asset_id=self.assetbundle_name,
            start=datetime.fromtimestamp(self.start_at / 1000, TIMEZONE),
            end=datetime.fromtimestamp(self.end_at / 1000, TIMEZONE),
            show_period=self.is_show_period,
            rarity_rates=[
                (RARITY[rate.card_rarity_type], rate.rate) for rate in self.gacha_card_rarity_rates
            ],
            card_weights=[(card.card_id, card.weight) for card in self.gacha_details],
            pickup_cards=[pickup.card_id for pickup in self.gacha_pickups],
            wish_cards=[card.card_id for card in self.gacha_details if card.is_wish],
        )
