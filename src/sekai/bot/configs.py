from datetime import timedelta
from enum import Enum

from sekai.api.master.helper.search import MatchMethod
from sekai.bot.config import Config


class UserApi(str, Enum):
    UNIPJSK = "unipjsk"


class MasterApi(str, Enum):
    PJSEKAI = "pjsekai"
    SEKAIWORLD = "sekaiworld"


class BotConfig(Config):
    token: str


class ServerConfig(Config):
    pjsekai_api: str | None = None
    sekaiworld_api: str | None = None
    unipjsk_api: str | None = None
    pjsekai_assets: str | None = None
    sekaiworld_assets: str | None = None
    user_api: UserApi = UserApi.UNIPJSK
    master_api: MasterApi = MasterApi.SEKAIWORLD
    check_cycle: timedelta = timedelta(hours=1)


class SearchConfig(Config):
    music: MatchMethod = MatchMethod.PART_PARTIAL_MATCH
    artist: MatchMethod = MatchMethod.PART_FULL_MATCH
    character: MatchMethod = MatchMethod.FULL_MATCH
    card: MatchMethod = MatchMethod.PART_PARTIAL_MATCH
    gacha: MatchMethod = MatchMethod.PART_PARTIAL_MATCH
    expiry: timedelta | None = timedelta(minutes=3)


class CommonConfig(Config):
    write_data_in_background: bool = True
