import contextlib

from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from sekai.bot import context
from sekai.bot.cmpnt import EventCallbackQuery, EventCommand
from sekai.bot.cmpnt.card.events import DeckEvent
from sekai.bot.cmpnt.user.events import AchievementEvent, ProfileEvent
from sekai.bot.utils.enum import humanize_enum
from sekai.core.models.live import LiveDifficulty

router = context.module_manager.create_router()


@router.callback_query(EventCallbackQuery(ProfileEvent))
@router.message(EventCommand("profile", event=ProfileEvent))
async def profile(update: Message | CallbackQuery, event: ProfileEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    message = await message.reply("Fetching data...")
    user = await context.user_api.get_user_info(event.id)
    buttons = [
        [
            InlineKeyboardButton(
                text="Achievements", callback_data=AchievementEvent(id=user.id).pack()
            ),
            InlineKeyboardButton(text="Main Deck", callback_data=DeckEvent(id=user.id).pack()),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.edit_text(
        f"""
<b>ID:</b> <code>{user.id}</code>
<b>Nickname:</b> <code>{user.profile.name}</code>
<b>Twitter (X):</b> <code>{user.profile.twitter}</code>
<b>Bio:</b> <code>{user.profile.bio}</code>
        """.strip(),
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()


@router.callback_query(EventCallbackQuery(AchievementEvent))
@router.message(EventCommand("achieve", event=AchievementEvent))
async def achievement(update: Message | CallbackQuery, event: ProfileEvent):
    def live_achievement(achievement: dict[LiveDifficulty, int]) -> str:
        return "\n".join(
            [f"・{humanize_enum(diff)}: {count}" for diff, count in achievement.items()]
        )

    assert (message := update if isinstance(update, Message) else update.message)
    message = await message.reply("Fetching data...")
    user = await context.user_api.get_user_info(event.id)
    achieve = await context.user_api.get_user_achievement(event.id)
    buttons = [
        [InlineKeyboardButton(text="Profile", callback_data=ProfileEvent(id=user.id).pack())]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.edit_text(
        f"""
<u><b><i>{user.profile.name}</i></b></u>
<b>Rank:</b> {achieve.rank}

<u><b>=== Live ===</b></u>
<b>Live Clear:</b> (Total: {sum(achieve.live.live_clears.values())})
{live_achievement(achieve.live.live_clears)}

<b>Full Combo:</b> (Total: {sum(achieve.live.full_combos.values())})
{live_achievement(achieve.live.full_combos)}

<b>All Perfect:</b> (Total: {sum(achieve.live.all_perfects.values())})
{live_achievement(achieve.live.all_perfects)}

<u><b>=== Multilive ===</b></u>
<b>MVP:</b> {achieve.multilive.mvp}
<b>Superstar:</b> {achieve.multilive.superstar}
        """.strip(),
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
