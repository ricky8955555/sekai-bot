from enum import Enum


def humanize_enum(enum: Enum):
    return enum.name.replace("_", " ").capitalize()
