from pydantic import BaseModel

from sekai.assets import CardPattern


class CardPhotoQuery(BaseModel):
    asset_id: str
    pattern: CardPattern

    def as_key(self) -> str:
        return f"{self.asset_id}_{self.pattern}"
