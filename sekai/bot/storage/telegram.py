from pathlib import Path
from typing import Generic, Sequence, TypeVar

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Audio, Document, File, Message, PhotoSize, Video

from sekai.bot.storage.mapping import MappingDataStorage, StorageStrategy

_KT = TypeVar("_KT")

FileObject = File | PhotoSize | Video | Audio | Document


class TelegramFileStorage(Generic[_KT]):
    _bot: Bot
    _files: MappingDataStorage[_KT, str]

    def __init__(
        self,
        key: type[_KT],
        bot: Bot,
        mapping_path: Path,
        strategy: StorageStrategy | None = None,
    ) -> None:
        self._bot = bot
        self._files = MappingDataStorage(key, str, mapping_path, strategy)

    async def _exists(self, file_id: str) -> bool:
        try:
            await self._bot.get_file(file_id)
            return True
        except TelegramBadRequest:
            return False

    @staticmethod
    def _extract_file(message: Message) -> FileObject | None:
        return (
            (message.photo[0] if message.photo else None)
            or message.video
            or message.document
            or message.audio
        )

    async def get(self, key: _KT) -> str | None:
        file_id = await self._files.get(key)
        if not file_id or not await self._exists(file_id):
            return None
        return file_id

    async def bind(self, key: _KT, file_id: str) -> None:
        await self._files.update(key, file_id)

    async def update(self, key: _KT, obj: Message | FileObject) -> None:
        file = self._extract_file(obj) if isinstance(obj, Message) else obj
        assert file, "object has no file."
        await self._files.update(key, file.file_id)

    async def update_all(self, keys: Sequence[_KT], objs: Sequence[Message | FileObject]) -> None:
        assert len(keys) == len(objs), "counts of 'keys' and 'messages' are not matched."
        file_objs = [self._extract_file(obj) if isinstance(obj, Message) else obj for obj in objs]
        assert all(file_objs), "not all objects have file."
        files = await self._files.load()
        files.update(zip(keys, (file.file_id for file in file_objs)))  # type: ignore
        await self._files.write(files)
