from enum import Enum


def humanize_enum(enum: Enum):
    return " ".join(enum.name.split("_")).capitalize()
