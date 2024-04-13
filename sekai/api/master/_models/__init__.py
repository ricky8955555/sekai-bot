from typing import TypeVar

import pydantic.alias_generators
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


AnyModel = TypeVar("AnyModel", bound=BaseSchema)
