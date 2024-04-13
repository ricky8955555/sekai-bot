from aiogram import Bot

from sekai.api.master.helper.cache import CachingMasterApi, CachingStrategy
from sekai.api.master.helper.search import make_master_api_search_helper
from sekai.api.master.pjsekai import PjsekaiApi
from sekai.api.master.sekaiworld import SekaiWorldApi
from sekai.api.user.unipjsk import UnipjskApi
from sekai.assets.helper import AssetHelper
from sekai.assets.pjsekai import PjsekaiAssets
from sekai.assets.sekaiworld import SekaiWorldAssets
from sekai.bot.configs import BotConfig, CommonConfig, MasterApi, SearchConfig, ServerConfig, UserApi
from sekai.bot.environ import cache_path, config_path
from sekai.bot.module import ModuleManager
from sekai.bot.storage import StorageStrategy

bot_config = BotConfig.load(config_path / "bot")
server_config = ServerConfig.load(config_path / "server")
search_config = SearchConfig.load(config_path / "search")
common_config = CommonConfig.load(config_path / "common")

bot: Bot

module_manager: ModuleManager

match server_config.master_api:
    case MasterApi.PJSEKAI:
        master_api = PjsekaiApi(server_config.pjsekai_api)
    case MasterApi.SEKAIWORLD:
        master_api = SekaiWorldApi(server_config.sekaiworld_api)

master_api = make_master_api_search_helper(CachingMasterApi)(
    # PjsekaiApi(server_config.pjsekai_api),
    master_api,
    cache_path,
    CachingStrategy(server_config.check_cycle),
)  # type: ignore

match server_config.user_api:
    case UserApi.UNIPJSK:
        user_api = UnipjskApi(server_config.unipjsk_api)

assets = AssetHelper(
    [
        SekaiWorldAssets(server_config.sekaiworld_assets),
        PjsekaiAssets(server_config.pjsekai_assets),
    ]
)  # type: ignore

storage_strategy = StorageStrategy(common_config.write_data_in_background)
