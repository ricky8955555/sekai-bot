from sekai.bot import context, environ
from sekai.bot.cmpnt.account.models import Account
from sekai.bot.storage.mapping import MappingDataStorage

accounts = MappingDataStorage(
    int,
    Account,
    environ.module_data_path / "account",
    context.storage_strategy,
)
