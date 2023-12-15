from pydantic import Field

from sekai.core.models import ToSharedModel
from sekai.core.models.chara import Character as SharedCharacter
from sekai.core.models.chara import Gender, Name

from . import BaseSchema


class Character(BaseSchema, ToSharedModel[SharedCharacter]):
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

    def to_shared_model(self) -> SharedCharacter:
        name = Name(first_name=self.first_name, given_name=self.given_name)
        return SharedCharacter(
            id=self.id,
            name=name,
            gender=Gender[self.gender.upper()],
            height=self.height,
        )
