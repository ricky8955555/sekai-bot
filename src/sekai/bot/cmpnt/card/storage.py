from sekai.bot import context, environ
from sekai.bot.cmpnt.card.models import CardPhotoQuery
from sekai.bot.storage.filesystem import FilesystemStorage

card_banners = FilesystemStorage[CardPhotoQuery](
    environ.file_storage_data_path / "card_banners",
    lambda query: context.assets.get_card_banner(query.asset_id, query.pattern),
)

card_cutouts = FilesystemStorage[CardPhotoQuery](
    environ.file_storage_data_path / "card_cutouts",
    lambda query: context.assets.get_card_cutout(query.asset_id, query.pattern),
)
