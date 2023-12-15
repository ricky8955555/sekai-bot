import contextlib
from io import BytesIO

from aiogram.enums import ParseMode
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from PIL import Image

from sekai.bot import context
from sekai.bot.events import EventCallbackQuery, EventCommand
from sekai.bot.events.music import MusicDownloadEvent, MusicDownloadType, MusicEvent
from sekai.bot.utils import humanize_enum
from sekai.core.models.music import MusicVersion

router = context.module_manager.create_router()


@router.callback_query(EventCallbackQuery(MusicEvent))
@router.message(EventCommand("music", event=MusicEvent))
async def music(update: Message | CallbackQuery, event: MusicEvent):
    async def version_singers(versions: list[MusicVersion]) -> list[list[str]]:
        all_singers = {singer for version in versions for singer in version.singers}
        all_charas = {
            singer: await context.pjsekai_api.get_character(singer) for singer in all_singers
        }
        return [
            [all_charas[singer].name.full_name for singer in version.singers]
            for version in versions
        ]

    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    music = await context.pjsekai_api.get_music_info(event.id)
    versions = await context.pjsekai_api.get_music_versions(event.id)
    ver_singers = await version_singers(versions)
    versions_str = "\n".join(
        f"・<b>{humanize_enum(version.vocal_type)} ver.</b> " f"({', '.join(singers)})"
        for version, singers in zip(versions, ver_singers)
    )
    levels = await context.pjsekai_api.get_music_difficulty_levels(event.id)
    diffculties = "\n".join(
        f"・<b>{humanize_enum(diff)}:</b> Lv.{level}" for diff, level in levels.items()
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


@router.callback_query(EventCallbackQuery(MusicDownloadEvent))
@router.message(EventCommand("musicdown", event=MusicDownloadEvent))
async def music_download(update: Message | CallbackQuery, event: MusicDownloadEvent):
    assert (message := update if isinstance(update, Message) else update.message)
    hint_message = await message.reply("waiting for handling...")
    version = await context.pjsekai_api.get_music_version(event.id)
    singers = [await context.pjsekai_api.get_character(singer) for singer in version.singers]
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
    music = await context.pjsekai_api.get_music_info(version.music_id)
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
