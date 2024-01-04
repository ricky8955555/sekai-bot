from typing import Generic, TypeVar

import pydantic.alias_generators
from pydantic import BaseModel, ConfigDict

AnyModel = TypeVar("AnyModel")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class BaseResponse(BaseSchema, Generic[AnyModel]):
    total: int
    limit: int
    skip: int
    data: list[AnyModel]
