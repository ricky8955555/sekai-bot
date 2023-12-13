from sekai.core.models import SharedModel


class Profile(SharedModel):
    name: str
    bio: str
    twitter: str


class UserInfo(SharedModel):
    id: int
    rank: int
    profile: Profile
