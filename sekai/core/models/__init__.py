import abc
from typing import Generic, TypeVar

from pydantic import BaseModel


class SharedModel(BaseModel):
    pass


T_Model = TypeVar("T_Model", bound=SharedModel)


class ToSharedModel(abc.ABC, Generic[T_Model]):
    @abc.abstractmethod
    def to_shared_model(self) -> T_Model:
        ...
