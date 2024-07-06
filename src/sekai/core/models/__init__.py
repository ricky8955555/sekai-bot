import abc
from typing import Generic, TypeVar

from pydantic import BaseModel


class SharedModel(BaseModel):
    pass


AnySharedModel = TypeVar("AnySharedModel", bound=SharedModel)


class ToSharedModel(abc.ABC, Generic[AnySharedModel]):
    @abc.abstractmethod
    def to_shared_model(self) -> AnySharedModel:
        ...
