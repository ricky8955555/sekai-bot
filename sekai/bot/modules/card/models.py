from pydantic import BaseModel

from sekai.assets import CardPattern


class CardPhotoQuery(BaseModel):
    asset_id: str
    pattern: CardPattern
    cutout: bool

    def __hash__(self) -> int:
        return hash(repr(self))
