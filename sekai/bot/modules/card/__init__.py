import contextlib

from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from sekai.assets import CardBannerType
from sekai.assets.exc import AssetNotFound
from sekai.bot import context
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.card import CardEvent, DeckEvent
from sekai.bot.utils.callback import CallbackQueryTaskManager
from sekai.core.models.card import CardRarity

router = context.module_manager.create_router()

tasks = CallbackQueryTaskManager(router, "card_task", "task is destroyed.")


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
    deck = await context.user_api.get_user_main_deck(event.id)
    cards = [await context.master_api.get_card_info(card.id) for card in deck.members]
    charas = [await context.master_api.get_character(card.character) for card in cards]
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
                (asset := await context.assets.get_card_cutout(card.asset_id)).data,
                f"{card.asset_id}.{asset.extension}",
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
<u><b><i>{deck.name}</i></b></u> (ID: {deck.id})

<u><b>=== Total Power ===</b></u>
・Area Item Bonus: {deck.total_power.area_item_bonus}
・Basic Card Total Power: {deck.total_power.basic_card_total_power}
・Character Rank Bonus: {deck.total_power.character_rank_bonus}
・Total Power: {deck.total_power.total_power}

<u><b>=== Members ===</b></u>
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
async def card_id(update: Message | CallbackQuery, event: CardEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    card = await context.master_api.get_card_info(event.id)
    character = await context.master_api.get_character(card.character)
    banners: list[InputMediaPhoto] = []
    for type in CardBannerType:
        with contextlib.suppress(AssetNotFound):
            banner = await context.assets.get_card_banner(card.asset_id, type)
            file = BufferedInputFile(banner.data, f"{type.name}.{banner.extension}")
            banners.append(InputMediaPhoto(media=file))
    messages = await message.reply_media_group(banners)  # type: ignore
    await messages[0].edit_caption(
        caption=f"""
<u><b>{card.title}</b></u>

ID: {card.id}
Character: {character.name}
Gender: {character.gender.name.capitalize()}
Height: {character.height} cm
Release Time: {card.released}
Rarity: {_RARITY[card.rarity]}
        """.strip(),
        parse_mode=ParseMode.HTML,
    )
    with contextlib.suppress(Exception):
        await hint_message.delete()
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()


async def card_search(message: Message, command: CommandObject):
    async def next_card(update: CallbackQuery | Message):
        assert (message := update if isinstance(update, Message) else update.message)
        if not (card := await anext(it, None)):
            if isinstance(update, Message):
                return await message.edit_text("no result found.")
            assert message.reply_markup
            buttons = message.reply_markup.inline_keyboard[0][:1]  # in known condition.
            markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await message.edit_reply_markup(reply_markup=markup)
            return await update.answer("no more result available.")
        task = tasks.create_task(next_card, expired_after=context.search_config.expiry)
        buttons = [
            InlineKeyboardButton(text="Detail", callback_data=CardEvent(id=card.id).pack()),
            InlineKeyboardButton(text="Next", callback_data=task.callback_data),
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
        character = await context.master_api.get_character(card.character)
        await message.edit_text(
            f"""
<u><b>{card.title}</b></u>

ID: {card.id}
Character: {character.name}
            """.strip(),
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )

    if not command.args:
        return
    message = await message.reply("waiting for handling...")
    it = aiter(
        context.master_api.search_card_info_by_title(command.args, context.search_config.card)
    )
    await next_card(message)


@router.message(Command("card"))
async def card(message: Message, command: CommandObject):
    with contextlib.suppress(TypeError, ValueError):
        event = CardEvent.from_command(command)
        return await card_id(message, event)
    return await card_search(message, command)
