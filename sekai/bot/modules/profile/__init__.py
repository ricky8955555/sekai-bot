from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from sekai.bot import context
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.card import DeckEvent
from sekai.bot.events.profile import ProfileEvent

router = context.module_manager.create_router()


@router.callback_query(EventCallbackQuery(ProfileEvent))
@router.message(EventCommand("profile", event=ProfileEvent))
async def profile(update: Message | CallbackQuery, event: ProfileEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    message = await message.reply("waiting for handling...")
    user = await context.uniprsk_api.get_user_info(event.id)
    buttons = [[InlineKeyboardButton(text="Main Deck", callback_data=DeckEvent(id=user.id).pack())]]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.edit_text(
        f"""
ID: {user.id}
Nickname: {user.profile.name}
Twitter (X): {user.profile.twitter}
Rank: {user.rank}
Bio: {user.profile.bio}
        """.strip(),
        reply_markup=markup,
    )
    if isinstance(update, CallbackQuery):
        await update.answer()
