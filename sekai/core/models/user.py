from sekai.core.models import SharedModel
from sekai.core.models.live import Difficulty


class Profile(SharedModel):
    name: str
    bio: str
    twitter: str


class UserInfo(SharedModel):
    id: int
    profile: Profile


class LiveAchievement(SharedModel):
    live_clears: dict[Difficulty, int]
    full_combos: dict[Difficulty, int]
    all_perfects: dict[Difficulty, int]


class MultiliveAchievement(SharedModel):
    mvp: int
    superstar: int


class Achievement(SharedModel):
    rank: int
    live: LiveAchievement
    multilive: MultiliveAchievement
