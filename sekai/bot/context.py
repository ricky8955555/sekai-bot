from aiogram import Bot

from sekai.api.helper.cache import CachingMasterApi, CachingStrategy
from sekai.api.helper.search import make_master_api_search_helper
from sekai.api.pjsekai import PjsekaiApi
from sekai.api.unipjsk import UnipjskApi
from sekai.assets.helper import AssetHelper
from sekai.assets.pjsekai import PjsekaiAssets
from sekai.assets.sekaiviewer import SekaiViewerAssets
from sekai.bot.configs import BotConfig, CommonConfig, SearchConfig, ServerConfig
from sekai.bot.environ import cache_path, config_path
from sekai.bot.module import ModuleManager
from sekai.bot.storage import StorageStrategy

bot_config = BotConfig.load(config_path / "bot")
server_config = ServerConfig.load(config_path / "server")
search_config = SearchConfig.load(config_path / "search")
common_config = CommonConfig.load(config_path / "common")

bot: Bot

module_manager: ModuleManager

master_api: CachingMasterApi = make_master_api_search_helper(CachingMasterApi)(
    PjsekaiApi(server_config.pjsekai_api),
    cache_path,
    CachingStrategy(server_config.check_cycle),
)  # type: ignore
user_api = UnipjskApi(server_config.uniprsk_api)

assets = AssetHelper(
    [
        SekaiViewerAssets(server_config.sekaiworld_assets),
        PjsekaiAssets(server_config.pjsekai_assets),
    ]
)  # type: ignore

storage_strategy = StorageStrategy(common_config.write_data_in_background)
