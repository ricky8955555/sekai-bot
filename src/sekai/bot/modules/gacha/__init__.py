import asyncio
import contextlib
import html
import io
from datetime import UTC, datetime
from typing import AsyncIterable

from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from PIL import Image

from sekai.assets import CardPattern
from sekai.bot import context
from sekai.bot.cmpnt import EventCallbackQuery, EventCommand
from sekai.bot.cmpnt.card.events import CardEvent
from sekai.bot.cmpnt.card.models import CardPhotoQuery
from sekai.bot.cmpnt.card.storage import card_banners
from sekai.bot.cmpnt.gacha import emulate
from sekai.bot.cmpnt.gacha.draw import draw_result
from sekai.bot.cmpnt.gacha.events import DoGachaEvent, GachaEvent
from sekai.bot.cmpnt.gacha.models import DoGachaType
from sekai.bot.cmpnt.gacha.storage import gacha_logos
from sekai.bot.constants import RARITY_EMOJIS
from sekai.bot.utils import textwrap
from sekai.bot.utils.callback import CallbackQueryTaskManager
from sekai.bot.utils.file import complete_filename
from sekai.core.models.card import CardRarity
from sekai.core.models.gacha import Gacha

router = context.module_manager.create_router()

tasks = CallbackQueryTaskManager(router, "gacha_task", "task is destroyed.")


@router.callback_query(EventCallbackQuery(GachaEvent))
async def gacha_id(update: Message | CallbackQuery, event: GachaEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("Fetching data...")
    gacha = await context.master_api.get_gacha(event.id)
    logo = await gacha_logos.get(gacha.asset_id)
    logo = BufferedInputFile(logo, complete_filename(gacha.asset_id, logo))
    pickups = [
        (
            (card := await context.master_api.get_card_info(pickup)),
            await context.master_api.get_game_character(card.character),
        )
        for pickup in gacha.pickup_cards
    ]
    pickup_infos = "\n".join(f"・{chara.name}: {card.title}" for card, chara in pickups)
    summary = textwrap.shorten(gacha.summary, 250)
    normal_rates = "\n".join(
        f"・{RARITY_EMOJIS[rarity]}: {rate} %"
        for rarity, rate in emulate.calculate_normal_rarity_rates(gacha).items()
    )
    guaranteed_rates = "\n".join(
        f"・{RARITY_EMOJIS[rarity]}: {rate} %"
        for rarity, rate in emulate.calculate_guaranteed_rarity_rates(
            gacha, CardRarity.THREE
        ).items()
    )
    card_buttons = [
        InlineKeyboardButton(
            text=f"{chara.name} ({card.title})", callback_data=CardEvent(id=card.id).pack()
        )
        for card, chara in pickups
    ]
    highest_rarity = max(rarity for rarity, _ in gacha.rarity_rates)
    dogacha_buttons = [
        InlineKeyboardButton(
            text=f"{RARITY_EMOJIS[CardRarity.THREE]} Guaranteed",
            callback_data=DoGachaEvent(id=gacha.id, type=DoGachaType.NORMAL).pack(),
        ),
        InlineKeyboardButton(
            text=f"{RARITY_EMOJIS[highest_rarity]} Guaranteed",
            callback_data=DoGachaEvent(id=gacha.id, type=DoGachaType.GUARANTEED).pack(),
        ),
    ]
    buttons = [[button] for button in card_buttons] + [dogacha_buttons]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await hint_message.edit_text("Uploading image...")
    message = await message.reply_photo(
        logo,
        f"""
<u><b><i>{gacha.name}</i></b></u>

<blockquote>{html.escape(summary)}</blockquote>

ID: {gacha.id}
Period: {gacha.start} - {gacha.end if gacha.show_period else ''}

Normal Rarity Rates:
{normal_rates}

Guaranteed Rarity Rates:
{guaranteed_rates}

Pickups:
{pickup_infos}
        """.strip(),
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
    )
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
    with contextlib.suppress(Exception):
        await hint_message.delete()


async def iter_gacha(message: Message, iterable: AsyncIterable[Gacha]):
    async def next_gacha(update: CallbackQuery | Message):
        assert (message := update if isinstance(update, Message) else update.message)
        if not (gacha := await anext(it, None)):
            if isinstance(update, Message):
                return await message.edit_text("No result found.")
            assert message.reply_markup
            buttons = message.reply_markup.inline_keyboard[0][:1]  # in known condition.
            markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await message.edit_reply_markup(reply_markup=markup)
            return await update.answer("No more result available.")
        task = tasks.create_task(next_gacha, expired_after=context.search_config.expiry)
        buttons = [
            [InlineKeyboardButton(text="Detail", callback_data=GachaEvent(id=gacha.id).pack())],
            [InlineKeyboardButton(text="Next", callback_data=task.callback_data)],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.edit_text(
            f"""
<u><b><i>{gacha.name}</i></b></u>

ID: {gacha.id}
Period: {gacha.start} - {gacha.end if gacha.show_period else ''}
            """,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )

    it = aiter(iterable)
    message = await message.reply("Fetching data...")
    await next_gacha(message)


@router.message(Command("nowgacha"))
async def now_gacha(message: Message):
    it = (
        gacha
        async for gacha in context.master_api.iter_gachas()
        if (now := datetime.now(UTC)) > gacha.start and now < gacha.end
    )
    return await iter_gacha(message, it)


async def gacha_search(message: Message, command: CommandObject):
    if not command.args:
        return
    return await iter_gacha(
        message, context.master_api.search_gacha_by_name(command.args, context.search_config.gacha)
    )


@router.message(Command("gacha"))
async def gacha(message: Message, command: CommandObject):
    with contextlib.suppress(TypeError, ValueError):
        event = CardEvent.from_command(command)
        return await gacha_id(message, event)
    return await gacha_search(message, command)


@router.callback_query(EventCallbackQuery(DoGachaEvent))
@router.message(EventCommand("dogacha", event=DoGachaEvent))
async def do_gacha(update: Message | CallbackQuery, event: DoGachaEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("Fetching data...")
    gacha = await context.master_api.get_gacha(event.id)
    await hint_message.edit_text("Emulating gacha...")
    match event.type:
        case DoGachaType.NORMAL:
            cards = await emulate.emulate_gacha(
                gacha.card_weights,
                (emulate.calculate_guaranteed_rarity_rates(gacha, CardRarity.THREE), 1),
                (emulate.calculate_normal_rarity_rates(gacha), 9),
            )
        case DoGachaType.GUARANTEED:
            highest = max(rarity for rarity, _ in gacha.rarity_rates)
            cards = await emulate.emulate_gacha(
                gacha.card_weights,
                (emulate.calculate_guaranteed_rarity_rates(gacha, highest), 1),
                (emulate.calculate_normal_rarity_rates(gacha), 9),
            )
    await hint_message.edit_text("Fetching card infos and banners...")
    charas = {
        chara: await context.master_api.get_game_character(chara)
        for chara in set(card.character for card in cards)
    }
    queries = [CardPhotoQuery(asset_id=card.asset_id, pattern=CardPattern.NORMAL) for card in cards]
    banners = await asyncio.gather(*map(card_banners.get, queries))
    await hint_message.edit_text("Generating result image...")
    banners = map(Image.open, map(io.BytesIO, banners))  # type: ignore
    result = io.BytesIO()
    with draw_result(list(zip(cards, banners))) as result_im:
        result_im.save(result, "PNG")
    for banner in banners:
        banner.close()
    result.seek(0)
    result = BufferedInputFile(
        result.read(), f"gacha_{gacha.id}_result_{datetime.now().timestamp()}.png"
    )
    caption = "\n".join(
        f"・{RARITY_EMOJIS[card.rarity]} {charas[card.character].name} - {card.title}"
        for card in cards
    )
    await hint_message.edit_text("Uploading image...")
    await message.reply_photo(result, caption=caption, parse_mode=ParseMode.HTML)
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
    with contextlib.suppress(Exception):
        await hint_message.delete()
