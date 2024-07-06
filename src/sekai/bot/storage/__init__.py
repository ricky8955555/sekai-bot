from dataclasses import dataclass


@dataclass(frozen=True)
class StorageStrategy:
    write_in_background: bool = True
