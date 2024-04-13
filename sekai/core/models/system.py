from sekai.core.models import SharedModel


class SystemInfo(SharedModel):
    profile: str
    app_version: str
    multilive_version: str
    data_version: str
    asset_version: str
    app_hash: str
    asset_hash: str
