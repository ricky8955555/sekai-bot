from datetime import datetime

from sekai.core.models import ToSharedModel
from sekai.core.models.system import SystemInfo as SharedSystemInfo

from . import BaseSchema


class SystemInfo(BaseSchema, ToSharedModel[SharedSystemInfo]):
    system_profile: str
    app_version: str
    multi_play_version: str
    data_version: str
    asset_version: str
    app_hash: str
    asset_hash: str
    app_version_status: str
    datetime: int

    def to_shared_model(self) -> SharedSystemInfo:
        return SharedSystemInfo(
            profile=self.system_profile,
            app_version=self.app_version,
            multilive_version=self.multi_play_version,
            data_version=self.data_version,
            asset_version=self.asset_version,
            app_hash=self.app_hash,
            asset_hash=self.asset_hash,
            published=datetime.utcfromtimestamp(self.datetime / 1000),  # type: ignore
        )
