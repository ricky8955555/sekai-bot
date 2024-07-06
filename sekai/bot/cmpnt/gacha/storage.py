from sekai.bot import context, environ
from sekai.bot.storage.filesystem import FilesystemStorage

gacha_logos = FilesystemStorage[str](
    environ.file_storage_data_path / "gacha_logo", context.assets.get_gacha_logo
)
