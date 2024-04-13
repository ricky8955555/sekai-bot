from typing import Generic

from .._models import AnyModel, BaseSchema


class BaseResponse(BaseSchema, Generic[AnyModel]):
    total: int
    limit: int
    skip: int
    data: list[AnyModel]
