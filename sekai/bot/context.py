from sekai.api.helper.cache import CachingMasterApi, CachingStrategy
from sekai.api.helper.search import make_master_api_search_helper
from sekai.api.pjsekai import PjsekaiApi
from sekai.api.unipjsk import UnipjskApi
from sekai.assets.helper import AssetHelper
from sekai.assets.pjsekai import PjsekaiAssets
from sekai.assets.sekaiviewer import SekaiViewerAssets
from sekai.bot.configs import BotConfig, SearchConfig, ServerConfig
from sekai.bot.environ import cache_path
from sekai.bot.module import ModuleManager

bot_config = BotConfig.load("bot")
server_config = ServerConfig.load("server")
search_config = SearchConfig.load("search")

module_manager: ModuleManager

master_api = make_master_api_search_helper(CachingMasterApi)(
    PjsekaiApi(server_config.pjsekai_api),
    cache_path,
    CachingStrategy(server_config.cache_expiry),
)  # type: ignore
user_api = UnipjskApi(server_config.uniprsk_api)

assets = AssetHelper(
    [
        SekaiViewerAssets(server_config.sekaiworld_assets),
        PjsekaiAssets(server_config.pjsekai_assets),
    ]
)  # type: ignore
