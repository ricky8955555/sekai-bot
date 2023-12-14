import contextlib

from aiogram.enums import ParseMode
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, InputMediaPhoto, Message)

from sekai.assets import CardBannerType
from sekai.assets.exc import AssetNotFound
from sekai.bot import context
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.card import CardEvent, DeckEvent
from sekai.core.models.card import CardRarity

router = context.module_manager.create_router()


_RARITY = {
    CardRarity.ONE: "⭐",
    CardRarity.TWO: "⭐⭐",
    CardRarity.THREE: "⭐⭐⭐",
    CardRarity.FOUR: "⭐⭐⭐⭐",
    CardRarity.BIRTHDAY: "🎀",
}


@router.callback_query(EventCallbackQuery(DeckEvent))
@router.message(EventCommand("deck", event=DeckEvent))
async def deck(update: Message | CallbackQuery, event: DeckEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    deck = await context.uniprsk_api.get_user_main_deck(event.id)
    cards = [await context.pjsekai_api.get_card_info(card.id) for card in deck.members]
    charas = [await context.pjsekai_api.get_character(card.character) for card in cards]
    buttons = [
        InlineKeyboardButton(
            text=chara.name.full_name,
            callback_data=CardEvent(
                id=card.id,
            ).pack(),
        )
        for card, chara in zip(cards, charas)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])
    cutouts = [
        InputMediaPhoto(
            media=BufferedInputFile(
                await context.pjsekai_assets.get_card_cutout(card.asset_id), card.asset_id
            )
        )
        for card in cards
    ]
    member_infos = [
        f"{chara.name} ("
        + f"Lv.{member.level}"
        + f", Master Rank: {member.master_rank}"
        + (", Special Trained" if member.special_trained else "")
        + ")"
        for (chara, member) in zip(charas, deck.members)
    ]
    messages = await message.reply_media_group(cutouts)  # type: ignore
    await messages[0].reply(
        f"""
<u><b>{deck.name}</b></u> (ID: {deck.id})

Total Power:
・Area Item Bonus: {deck.total_power.area_item_bonus}
・Basic Card Total Power: {deck.total_power.basic_card_total_power}
・Character Rank Bonus: {deck.total_power.character_rank_bonus}
・Total Power: {deck.total_power.total_power}

Members:
・Leader: {member_infos[0]}
・Subleader: {member_infos[1]}
・Member 3: {member_infos[2]}
・Member 4: {member_infos[3]}
・Member 5: {member_infos[4]}
        """.strip(),
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
    )
    with contextlib.suppress(Exception):
        await hint_message.delete()
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()


@router.callback_query(EventCallbackQuery(CardEvent))
@router.message(EventCommand("card", event=CardEvent))
async def card(update: Message | CallbackQuery, event: CardEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    card = await context.pjsekai_api.get_card_info(event.id)
    character = await context.pjsekai_api.get_character(card.character)
    banners: list[InputMediaPhoto] = []
    for type in CardBannerType:
        with contextlib.suppress(AssetNotFound):
            banner = await context.pjsekai_assets.get_card_banner(card.asset_id, type)
            file = BufferedInputFile(banner, type.name)
            banners.append(InputMediaPhoto(media=file))
    messages = await message.reply_media_group(banners)  # type: ignore
    await messages[0].edit_caption(
        caption=f"""
<u><b>{card.title}</b></u>

ID: {card.id}
Character: {character.name}
Gender: {character.gender.name.capitalize()}
Height: {character.height} cm
Release Date: {card.release}
Rarity: {_RARITY[card.rarity]}
        """.strip(),
        parse_mode=ParseMode.HTML,
    )
    with contextlib.suppress(Exception):
        await hint_message.delete()
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
