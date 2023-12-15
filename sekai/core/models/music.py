from datetime import datetime
from enum import IntEnum, auto

from sekai.core.models import SharedModel


class VocalType(IntEnum):
    SEKAI = auto()
    VIRTUAL_SINGER = auto()
    OTHER = auto()


class MusicVersion(SharedModel):
    id: int
    music_id: int
    vocal_type: VocalType
    singers: list[int]
    asset_id: str


class MusicInfo(SharedModel):
    title: str
    lyricist: str
    composer: str
    arranger: str
    released: datetime
    published: datetime
    asset_id: str
