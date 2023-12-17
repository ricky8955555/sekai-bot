from datetime import timedelta

from sekai.api.helper.search import MatchMethod
from sekai.bot.config import Config


class BotConfig(Config):
    token: str


class ServerConfig(Config):
    pjsekai_api: str | None = None
    uniprsk_api: str | None = None
    pjsekai_assets: str | None = None
    sekaiworld_assets: str | None = None
    cache_expiry: timedelta = timedelta(days=1)


class SearchConfig(Config):
    music: MatchMethod = MatchMethod.SPLIT_PART_PARTIAL_MATCH
    character: MatchMethod = MatchMethod.FULL_MATCH
    card: MatchMethod = MatchMethod.SPLIT_PART_PARTIAL_MATCH
    expiry: timedelta | None = timedelta(minutes=3)
