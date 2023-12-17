from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as
from typing_extensions import Self

from sekai.bot.environ import config_path


class Config(BaseModel):
    @classmethod
    def load(cls, name: str) -> Self:
        path = (config_path / name).with_suffix(".yaml")
        path = path.with_suffix(".yml") if not path.exists() else path
        if path.exists():
            return parse_yaml_file_as(cls, path)
        return cls()
