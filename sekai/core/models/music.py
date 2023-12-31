from datetime import datetime
from enum import IntEnum, auto

from sekai.core.models import SharedModel
from sekai.core.models.chara import Character


class VocalType(IntEnum):
    SEKAI = auto()
    VIRTUAL_SINGER = auto()
    OTHER = auto()


class MusicVersion(SharedModel):
    id: int
    music_id: int
    vocal_type: VocalType
    singers: list[Character]
    asset_id: str


class MusicInfo(SharedModel):
    id: int
    title: str
    lyricist: str
    composer: str
    arranger: str
    released: datetime
    published: datetime
    asset_id: str
