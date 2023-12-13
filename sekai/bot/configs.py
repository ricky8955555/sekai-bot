from sekai.bot.config import Config


class BotConfig(Config):
    token: str


class ServerConfig(Config):
    pjsekai_api: str | None = None
    uniprsk_api: str | None = None
    pjsekai_assets: str | None = None
