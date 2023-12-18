import contextlib
from io import BytesIO
from typing import AsyncIterable, Callable

from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from PIL import Image

from sekai.api.helper.search import MatchMethod
from sekai.bot import context
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.music import MusicDownloadEvent, MusicDownloadType, MusicEvent
from sekai.bot.utils.callback import CallbackQueryTaskManager
from sekai.bot.utils.enum import humanize_enum
from sekai.core.models.music import MusicInfo, MusicVersion

router = context.module_manager.create_router()

tasks = CallbackQueryTaskManager(router, "music_task", "task is destroyed.")


@router.callback_query(EventCallbackQuery(MusicEvent))
async def music_id(update: Message | CallbackQuery, event: MusicEvent):
    async def version_singers(versions: list[MusicVersion]) -> list[list[str]]:
        all_singers = {singer for version in versions for singer in version.singers}
        all_charas = {
            singer: await context.master_api.get_character(singer) for singer in all_singers
        }
        return [
            [all_charas[singer].name.full_name for singer in version.singers]
            for version in versions
        ]

    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    music = await context.master_api.get_music_info(event.id)
    versions = await context.master_api.get_versions_of_music(event.id)
    ver_singers = await version_singers(versions)
    versions_str = "\n".join(
        f"・<b>{humanize_enum(version.vocal_type)} ver.</b> " f"({', '.join(singers)})"
        for version, singers in zip(versions, ver_singers)
    )
    lives = await context.master_api.get_live_infos_of_music(event.id)
    diffculties = "\n".join(
        f"・<b>{humanize_enum(live.difficulty)}:</b> Lv.{live.level}" for live in lives
    )
    cover = await context.assets.get_music_cover(music.asset_id)
    cover_file = BufferedInputFile(cover.data, f"{music.asset_id}.{cover.extension}")
    buttons = [
        InlineKeyboardButton(
            text=(f"{humanize_enum(version.vocal_type)} ver. " f"({', '.join(singers)})"),
            callback_data=MusicDownloadEvent(id=version.id, type=MusicDownloadType.PREVIEW).pack(),
        )
        for version, singers in zip(versions, ver_singers)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[[button] for button in buttons])
    await message.reply_photo(
        cover_file,
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


async def music_search(
    message: Message,
    command: CommandObject,
    *,
    search_music_info: Callable[[str, MatchMethod], AsyncIterable[MusicInfo]] =
        context.master_api.search_music_info_by_title,
):
    async def next_music(update: CallbackQuery | Message):
        assert (message := update if isinstance(update, Message) else update.message)
        if not (music := await anext(it, None)):
            if isinstance(update, Message):
                return await message.edit_text("no result found.")
            assert message.reply_markup
            buttons = message.reply_markup.inline_keyboard[0][:1]  # in known condition.
            markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await message.edit_reply_markup(reply_markup=markup)
            return await update.answer("no more result available.")
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

    if not command.args:
        return
    message = await message.reply("waiting for handling...")
    it = aiter(search_music_info(command.args, context.search_config.music))
    await next_music(message)


@router.message(Command("music"))
async def music(message: Message, command: CommandObject):
    with contextlib.suppress(TypeError, ValueError):
        event = MusicEvent.from_command(command)
        return await music_id(message, event)
    return await music_search(message, command)


@router.message(Command("artist"))
async def artist(message: Message, command: CommandObject):
    return await music_search(
        message,
        command,
        search_music_info=context.master_api.search_music_info_by_artist,
    )


@router.callback_query(EventCallbackQuery(MusicDownloadEvent))
@router.message(EventCommand("musicdown", event=MusicDownloadEvent))
async def music_download(update: Message | CallbackQuery, event: MusicDownloadEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    version = await context.master_api.get_music_version(event.id)
    singers = [await context.master_api.get_character(singer) for singer in version.singers]
    match event.type:
        case MusicDownloadType.FULL:
            music_asset = await context.assets.get_music(version.asset_id)
            buttons = []
            caption = "It is normal to have a blank at the beginning of the music."
        case MusicDownloadType.PREVIEW:
            music_asset = await context.assets.get_music_preview(version.asset_id)
            buttons = [
                InlineKeyboardButton(
                    text="Download Full Version",
                    callback_data=MusicDownloadEvent(
                        id=event.id, type=MusicDownloadType.FULL
                    ).pack(),
                )
            ]
            caption = None
    singers_str = ", ".join(singer.name.full_name for singer in singers)
    music = await context.master_api.get_music_info(version.music_id)
    filename = f"{singers_str} - {music.title}.{music_asset.extension}"
    music_file = BufferedInputFile(music_asset.data, filename)
    cover = await context.assets.get_music_cover(music.asset_id)
    image = Image.open(BytesIO(cover.data)).convert("RGB")
    if factor := max(image.size) // 300:
        image = image.reduce(factor)
    image_bytes = BytesIO()
    image.save(image_bytes, "jpeg")
    cover_file = BufferedInputFile(image_bytes.getvalue(), f"{music.asset_id}.jpg")
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.reply_audio(
        music_file,
        caption,
        performer=singers_str,
        title=music.title,
        thumbnail=cover_file,
        reply_markup=markup,
    )
    with contextlib.suppress(Exception):
        if isinstance(update, CallbackQuery):
            await update.answer()
    with contextlib.suppress(Exception):
        await hint_message.delete()
