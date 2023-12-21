from pathlib import Path

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as
from typing_extensions import Self


class Config(BaseModel):
    @classmethod
    def load(cls, path: Path) -> Self:
        path = path if path.suffix else path.with_suffix(".yaml")
        path = path.with_suffix(".yml") if not path.exists() else path
        if path.exists():
            return parse_yaml_file_as(cls, path)
        return cls()
