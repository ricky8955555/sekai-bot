from enum import IntEnum, auto

from pydantic import BaseModel


class MusicDownloadType(IntEnum):
    FULL = auto()
    PREVIEW = auto()


class AudioQuery(BaseModel):
    version_id: int
    type: MusicDownloadType

    def as_key(self) -> str:
        return f"{self.version_id}_{self.type}"
