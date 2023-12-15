import contextlib
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from sekai.bot import context
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.card import DeckEvent
from sekai.bot.events.user import AchievementEvent, ProfileEvent
from sekai.core.models.live import Difficulty

router = context.module_manager.create_router()


@router.callback_query(EventCallbackQuery(ProfileEvent))
@router.message(EventCommand("profile", event=ProfileEvent))
async def profile(update: Message | CallbackQuery, event: ProfileEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    message = await message.reply("waiting for handling...")
    user = await context.uniprsk_api.get_user_info(event.id)
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
    def live_achievement(achievement: dict[Difficulty, int]) -> str:
        return "\n".join(
            [f"・{diff.name.capitalize()}: {count}" for diff, count in achievement.items()]
        )

    assert (message := update if isinstance(update, Message) else update.message)
    message = await message.reply("waiting for handling...")
    user = await context.uniprsk_api.get_user_info(event.id)
    achieve = await context.uniprsk_api.get_user_achievement(event.id)
    buttons = [
        [InlineKeyboardButton(text="Profile", callback_data=ProfileEvent(id=user.id).pack())]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.edit_text(
        f"""
<u><b><i>{user.profile.name}</i> Achievements</b></u>

<b>Rank:</b> {achieve.rank}

<b>Live Clear:</b> (Total: {sum(achieve.live_clears.values())})
{live_achievement(achieve.live_clears)}

<b>Full Combo:</b> (Total: {sum(achieve.full_combos.values())})
{live_achievement(achieve.full_combos)}

<b>All Perfect:</b> (Total: {sum(achieve.all_perfects.values())})
{live_achievement(achieve.all_perfects)}
        """.strip(),
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
