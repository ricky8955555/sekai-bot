from datetime import timedelta

from sekai.utils.config import Config


class ServerConfig(Config):
    cache_ttl: timedelta = timedelta(minutes=5.0)
