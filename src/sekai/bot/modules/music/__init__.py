import contextlib
from typing import AsyncIterable

from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from sekai.bot import context
from sekai.bot.cmpnt import EventCallbackQuery, EventCommand
from sekai.bot.cmpnt.music.events import MusicDownloadEvent, MusicEvent
from sekai.bot.cmpnt.music.models import AudioQuery, MusicDownloadType
from sekai.bot.cmpnt.music.storage import music_audios, music_covers
from sekai.bot.utils.callback import CallbackQueryTaskManager
from sekai.bot.utils.enum import humanize_enum
from sekai.bot.utils.file import complete_filename
from sekai.core.models.music import MusicInfo, MusicVersion

router = context.module_manager.create_router()

tasks = CallbackQueryTaskManager(router, "music_task", "task is destroyed.")


@router.callback_query(EventCallbackQuery(MusicEvent))
async def music_id(update: Message | CallbackQuery, event: MusicEvent):
    async def version_singers(versions: list[MusicVersion]) -> list[list[str]]:
        all_singers = [singer for version in versions for singer in version.singers]
        all_singers = [
            all_singers[i]
            for i in range(len(all_singers))
            if i == all_singers.index(all_singers[i])
        ]
        all_charas = [await context.master_api.get_character_info(singer) for singer in all_singers]
        return [
            [all_charas[all_singers.index(singer)].name for singer in version.singers]
            for version in versions
        ]

    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("Fetching data...")
    music = await context.master_api.get_music_info(event.id)
    versions = [version async for version in context.master_api.iter_versions_of_music(event.id)]
    ver_singers = await version_singers(versions)
    versions_str = "\n".join(
        f"・<b>{humanize_enum(version.vocal_type)} ver.</b> " f"({', '.join(singers)})"
        for version, singers in zip(versions, ver_singers)
    )
    lives = [live async for live in context.master_api.iter_live_infos_of_music(event.id)]
    diffculties = "\n".join(
        f"・<b>{humanize_enum(live.difficulty)}:</b> Lv.{live.level}" for live in lives
    )
    await hint_message.edit_text("Fetching music cover...")
    cover = await music_covers.get(music.asset_id)
    cover = BufferedInputFile(cover, complete_filename(music.asset_id, cover))
    buttons = [
        InlineKeyboardButton(
            text=(f"{humanize_enum(version.vocal_type)} ver. " f"({', '.join(singers)})"),
            callback_data=MusicDownloadEvent(id=version.id, type=MusicDownloadType.PREVIEW).pack(),
        )
        for version, singers in zip(versions, ver_singers)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[[button] for button in buttons])
    await hint_message.edit_text("Uploading image...")
    message = await message.reply_photo(
        cover,
        f"""
<u><b><i>{music.title}</i></b></u>

<u><b>=== Information ===</b></u>
・<b>Composer:</b> {music.composer}
・<b>Arranger:</b> {music.arranger}
・<b>Lyricist:</b> {music.lyricist}
・<b>Publish Time:</b> {music.published}
・<b>Release Time:</b> {music.released}

<u><b>=== Versions ===</b></u>
{versions_str}

<u><b>=== Difficulties ===</b></u>
{diffculties}
        """.strip(),
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
    )
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
    with contextlib.suppress(Exception):
        await hint_message.delete()


async def iter_music(message: Message, iterable: AsyncIterable[MusicInfo]):
    async def next_music(update: CallbackQuery | Message):
        assert (message := update if isinstance(update, Message) else update.message)
        if not (music := await anext(it, None)):
            if isinstance(update, Message):
                return await message.edit_text("No result found.")
            assert message.reply_markup
            buttons = message.reply_markup.inline_keyboard[0][:1]  # in known condition.
            markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await message.edit_reply_markup(reply_markup=markup)
            return await update.answer("No more result available.")
        task = tasks.create_task(next_music, expired_after=context.search_config.expiry)
        buttons = [
            InlineKeyboardButton(text="Detail", callback_data=MusicEvent(id=music.id).pack()),
            InlineKeyboardButton(text="Next", callback_data=task.callback_data),
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.edit_text(
            f"""
<u><b><i>{music.title}</i></b></u>

<u><b>=== Information ===</b></u>
・<b>Composer:</b> {music.composer}
・<b>Arranger:</b> {music.arranger}
・<b>Lyricist:</b> {music.lyricist}
            """.strip(),
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )

    message = await message.reply("Fetching data...")
    it = aiter(iterable)
    await next_music(message)


@router.message(Command("music"))
async def music(message: Message, command: CommandObject):
    if not command.args:
        return
    with contextlib.suppress(TypeError, ValueError):
        event = MusicEvent.from_command(command)
        return await music_id(message, event)
    return await iter_music(
        message,
        context.master_api.search_music_info_by_title(command.args, context.search_config.music),
    )


@router.message(Command("artist"))
async def artist(message: Message, command: CommandObject):
    if not command.args:
        return
    return await iter_music(
        message,
        context.master_api.search_music_info_by_artist(command.args, context.search_config.artist),
    )


@router.callback_query(EventCallbackQuery(MusicDownloadEvent))
@router.message(EventCommand("musicdown", event=MusicDownloadEvent))
async def music_download(update: Message | CallbackQuery, event: MusicDownloadEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("Fetching audio...")
    query = AudioQuery(version_id=event.id, type=event.type)
    audio = await music_audios.get(query)
    audio = BufferedInputFile(audio, complete_filename(str(query.version_id), audio))
    buttons = []
    if event.type == MusicDownloadType.PREVIEW:
        buttons.append(
            InlineKeyboardButton(
                text="Download Full Version",
                callback_data=MusicDownloadEvent(id=event.id, type=MusicDownloadType.FULL).pack(),
            )
        )
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await hint_message.edit_text("Uploading audio...")
    message = await message.reply_audio(audio, reply_markup=markup)
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
    with contextlib.suppress(Exception):
        await hint_message.delete()
