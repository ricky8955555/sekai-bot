from sekai.core.models import SharedModel
from sekai.core.models.live import Difficulty


class Profile(SharedModel):
    name: str
    bio: str
    twitter: str


class UserInfo(SharedModel):
    id: int
    profile: Profile


class Achievement(SharedModel):
    rank: int
    live_clears: dict[Difficulty, int]
    full_combos: dict[Difficulty, int]
    all_perfects: dict[Difficulty, int]
