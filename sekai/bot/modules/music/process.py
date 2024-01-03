from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from aiofile import async_open
from ffmpeg.asyncio import FFmpeg
from ffmpeg.types import Option

from sekai.assets import Asset


@dataclass(frozen=True)
class Metadata:
    title: str
    composer: str
    artist: str
    cover: Asset | None = None


async def resize_cover(cover: Asset) -> Asset:
    with TemporaryDirectory() as dir:
        dir = Path(dir)
        input_file = (dir / "audio").with_suffix(cover.extension)
        output_file = dir / "output.jpg"
        async with async_open(input_file, "wb") as fp:
            await fp.write(cover.data)
        ffmpeg = FFmpeg().input(input_file).output(output_file)
        await ffmpeg.execute()
        async with async_open(input_file, "rb") as fp:
            data = await fp.read()
    return Asset(data, ".jpg")


async def process_audio(music: Asset, metadata: Metadata, offset: float = 0) -> Asset:
    with TemporaryDirectory() as dir:
        dir = Path(dir)
        input_file = (dir / "audio").with_suffix(music.extension)
        output_file = dir / "output.mp3"
        ffmpeg = FFmpeg().option("y")
        options: dict[str, Option | None] = {}
        async with async_open(input_file, "wb") as fp:
            await fp.write(music.data)
        ffmpeg.input(input_file, ss=offset)
        if music.extension == ".mp3":
            options["c:a"] = "copy"
        else:
            options["c:a"] = "libmp3lame"
            options["V"] = 0
        if metadata.cover:
            cover_file = (dir / "cover").with_suffix(metadata.cover.extension)
            async with async_open(cover_file, "wb") as fp:
                await fp.write(metadata.cover.data)
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
        async with async_open(output_file, "rb") as fp:
            data = await fp.read()
    return Asset(data, ".mp3")
