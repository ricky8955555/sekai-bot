from sekai.bot import context, environ
from sekai.bot.cmpnt.music import process
from sekai.bot.cmpnt.music.models import AudioQuery
from sekai.bot.storage.filesystem import FilesystemStorage

music_audios = FilesystemStorage[AudioQuery](
    environ.file_storage_data_path / "music_audio", process.fetch_and_process_audio
)

music_covers = FilesystemStorage[str](
    environ.file_storage_data_path / "music_cover", context.assets.get_music_cover
)
