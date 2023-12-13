from sekai.api.pjsekai import PjsekaiApi
from sekai.api.unipjsk import UnipjskApi
from sekai.assets.pjsekai import PjsekaiAssets
from sekai.bot.configs import BotConfig, ServerConfig
from sekai.bot.module import ModuleManager

bot_config = BotConfig.load("bot")
server_config = ServerConfig.load("server")

module_manager: ModuleManager

pjsekai_api = PjsekaiApi(server_config.pjsekai_api)
uniprsk_api = UnipjskApi(server_config.uniprsk_api)

pjsekai_assets = PjsekaiAssets(server_config.pjsekai_assets)
