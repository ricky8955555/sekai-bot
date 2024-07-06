from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import magic
from aiofile import async_open
from ffmpeg.asyncio import FFmpeg
from ffmpeg.types import Option

from sekai.bot import context
from sekai.bot.cmpnt.music.models import AudioQuery, MusicDownloadType


@dataclass(frozen=True)
class Metadata:
    title: str
    composer: str
    artist: str
    cover: bytes | None = None


async def resize_cover(cover: bytes) -> bytes:
    with TemporaryDirectory() as dir:
        dir = Path(dir)
        input_file = dir / "audio"
        output_file = dir / "output.jpg"
        async with async_open(input_file, "wb") as afp:
            await afp.write(cover)
        ffmpeg = FFmpeg().input(input_file).output(output_file)
        await ffmpeg.execute()
        async with async_open(input_file, "rb") as afp:
            data = await afp.read()
    return data


async def process_audio(music: bytes, metadata: Metadata, offset: float = 0) -> bytes:
    with TemporaryDirectory() as dir:
        dir = Path(dir)
        input_file = dir / "audio"
        output_file = dir / "output.mp3"
        ffmpeg = FFmpeg().option("y")
        options: dict[str, Option | None] = {}
        async with async_open(input_file, "wb") as afp:
            await afp.write(music)
        ffmpeg.input(input_file, ss=offset)
        mime = magic.from_file(input_file, True)
        if mime == "audio/mpeg":
            options["c:a"] = "copy"
        else:
            options["c:a"] = "libmp3lame"
            options["V"] = 0
        if metadata.cover:
            cover_file = dir / "cover"
            async with async_open(cover_file, "wb") as afp:
                await afp.write(metadata.cover)
            ffmpeg.input(cover_file)
            options["map"] = [0, 1]
            options["c:v"] = "copy"
        options["metadata"] = [
            f"title={metadata.title}",
            f"artist={metadata.artist}",
            f"composer={metadata.composer}",
        ]
        ffmpeg.output(output_file, options)
        await ffmpeg.execute()
        async with async_open(output_file, "rb") as afp:
            data = await afp.read()
    return data


async def fetch_and_process_audio(query: AudioQuery) -> bytes:
    version = await context.master_api.get_music_version(query.version_id)
    singers = [await context.master_api.get_character_info(singer) for singer in version.singers]
    music = await context.master_api.get_music_info(version.music_id)
    match query.type:
        case MusicDownloadType.FULL:
            audio = await context.assets.get_music(version.asset_id)
            offset = 8.0
        case MusicDownloadType.PREVIEW:
            audio = await context.assets.get_music_preview(version.asset_id)
            offset = 0.0
    artists = "/".join(singer.name for singer in singers)
    cover = await context.assets.get_music_cover(music.asset_id)
    metadata = Metadata(music.title, music.composer, artists, cover)
    processed = await process_audio(audio, metadata, offset)
    return processed


async def fetch_and_resize_cover(asset_id: str) -> bytes:
    cover = await context.assets.get_music_cover(asset_id)
    resized = await resize_cover(cover)
    return resized
