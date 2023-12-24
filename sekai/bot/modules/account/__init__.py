from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from sekai.bot import context, environ
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.account import AccountBindEvent
from sekai.bot.events.card import DeckEvent
from sekai.bot.events.user import AchievementEvent, ProfileEvent
from sekai.bot.storage import MappingDataStorage

from .models import Account

router = context.module_manager.create_router()

accounts = MappingDataStorage[int, Account](
    environ.module_data_path / "account",
    context.storage_strategy,
)


@router.callback_query(EventCallbackQuery(AccountBindEvent))
@router.message(EventCommand("bind", event=AccountBindEvent))
async def bind(update: Message | CallbackQuery, event: AccountBindEvent):
    if isinstance(update, Message) and (update.sender_chat or not update.from_user):
        return await update.reply("binding to anonymous chat is not supported.")
    assert (message := update if isinstance(update, Message) else update.message)
    target = update.from_user.id  # type: ignore
    account = Account(user_id=event.id)
    await accounts.update(target, account)
    await message.reply(
        f"your account is successfully bound with user <code>{event.id}</code>.",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("account"))
async def account(message: Message):
    target = message.reply_to_message or message
    if target.sender_chat or not target.from_user:
        return await message.reply("binding to anonymous chat is not supported.")
    account = await accounts.get(target.from_user.id)
    if not account:
        return await message.reply("user has no account binding.")
    buttons = [
        InlineKeyboardButton(text="Profile", callback_data=ProfileEvent(id=account.user_id).pack()),
        InlineKeyboardButton(
            text="Achievements", callback_data=AchievementEvent(id=account.user_id).pack()
        ),
        InlineKeyboardButton(text="Deck", callback_data=DeckEvent(id=account.user_id).pack()),
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.reply(
        "please choose the item to query.",
        reply_markup=markup,
    )
