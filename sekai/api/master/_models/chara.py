from pydantic import Field

from sekai.core.models import ToSharedModel
from sekai.core.models.chara import ExtraCharacter
from sekai.core.models.chara import GameCharacter as SharedGameCharacter
from sekai.core.models.chara import Gender

from . import BaseSchema


class GameCharacter(BaseSchema, ToSharedModel[SharedGameCharacter]):
    id: int
    seq: int
    resource_id: int
    first_name: str | None = None
    given_name: str
    first_name_ruby: str | None = None
    given_name_ruby: str
    gender: str
    height: int
    live2d_height_adjustment: int = Field(alias="live2dHeightAdjustment")
    figure: str
    breast_size: str
    # Field "model_name" has conflict with protected namespace "model_".
    chara_model_name: str = Field(alias="modelName")
    unit: str
    support_unit_type: str

    def to_shared_model(self) -> SharedGameCharacter:
        return SharedGameCharacter(
            id=self.id,
            name=f"{self.first_name or ''}{self.given_name}",
            gender=Gender[self.gender.upper()],
            height=self.height,
        )


class OutsideCharacter(BaseSchema, ToSharedModel[ExtraCharacter]):
    id: int
    seq: int
    name: str

    def to_shared_model(self) -> ExtraCharacter:
        return ExtraCharacter(
            id=self.id,
            name=self.name,
        )
