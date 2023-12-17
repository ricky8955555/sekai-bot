from sekai.core.models import SharedModel
from sekai.core.models.live import LiveDifficulty


class Profile(SharedModel):
    name: str
    bio: str
    twitter: str


class UserInfo(SharedModel):
    id: int
    profile: Profile


class LiveAchievement(SharedModel):
    live_clears: dict[LiveDifficulty, int]
    full_combos: dict[LiveDifficulty, int]
    all_perfects: dict[LiveDifficulty, int]


class MultiliveAchievement(SharedModel):
    mvp: int
    superstar: int


class Achievement(SharedModel):
    rank: int
    live: LiveAchievement
    multilive: MultiliveAchievement
