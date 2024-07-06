import asyncio
import itertools
import random
from typing import Mapping, Sequence

from sekai.bot import context
from sekai.core.models.card import CardInfo, CardRarity
from sekai.core.models.gacha import Gacha


def calculate_normal_rarity_rates(gacha: Gacha) -> dict[CardRarity, float]:
    return dict(gacha.rarity_rates)


def calculate_guaranteed_rarity_rates(
    gacha: Gacha, guarantee_for: CardRarity
) -> dict[CardRarity, float]:
    rates = dict(gacha.rarity_rates)
    assert guarantee_for in rates, f"{guarantee_for} not found in gacha."
    nonguaranteed = 0
    for rarity in set(rates.keys()):
        if rarity >= guarantee_for:
            continue
        nonguaranteed += rates[rarity]
        rates[rarity] = 0
    rates[guarantee_for] += nonguaranteed
    return rates


async def emulate_gacha(
    card_weights: Sequence[tuple[int, int]],
    *plan: tuple[Mapping[CardRarity, float], int],
    rand: random.Random | None = None,
) -> list[CardInfo]:
    cards, weights = zip(*card_weights)
    cards = await asyncio.gather(*map(context.master_api.get_card_info, cards))
    groups = {
        rarity: list(zip(*cards))
        for rarity, cards in (
            itertools.groupby(
                sorted(zip(cards, weights), key=lambda x: x[0].rarity), lambda x: x[0].rarity
            )
        )
    }
    rand = rand or random.Random(None)
    results: list[CardInfo] = []
    for rates, count in plan:
        rarities, weights = list(rates.keys()), list(rates.values())
        results.extend(
            rand.choices(*groups[rand.choices(rarities, weights)[0]])[0] for _ in range(count)
        )
    return results
