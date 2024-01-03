from pydantic import BaseModel

from sekai.bot.events.music import MusicDownloadType


class AudioQuery(BaseModel):
    asset_id: str
    type: MusicDownloadType

    def __hash__(self) -> int:
        return hash(repr(self))
