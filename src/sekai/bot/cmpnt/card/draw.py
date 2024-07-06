import operator
from typing import cast

from PIL import Image
from PIL.Image import Image as ImageType

from sekai.assets import CardPattern
from sekai.bot import environ
from sekai.bot.utils import image
from sekai.core.models.card import CardAttribute, CardInfo, CardRarity


def _relative_size(size: tuple[int, int], factor: tuple[float, float]) -> tuple[int, int]:
    return cast(tuple[int, int], tuple(map(int, map(operator.mul, size, factor))))


def _draw_rarity_birthday(im: ImageType, size: float, margin: tuple[float, float]) -> None:
    margin = _relative_size(im.size, margin)
    with Image.open(environ.resource_path / "rarity" / "birthday.png") as icon:
        icon = image.relative_resize(icon, im.size, size)
        im.paste(icon, (margin[0], im.size[1] - margin[1] - icon.size[1]), icon)


def _draw_rarity_normal(
    im: ImageType, rarity: int, pattern: CardPattern, size: float, margin: tuple[float, float]
) -> None:
    name = f"{pattern.name.lower()}.png"
    margin = _relative_size(im.size, margin)
    with Image.open(environ.resource_path / "rarity" / name) as icon:
        icon = image.relative_resize(icon, im.size, size)
        for i in range(rarity):
            y = im.size[1] - margin[1] - ((i + 1) * icon.size[1])
            im.paste(icon, (margin[0], y), icon)


def _draw_attr(
    im: ImageType, attr: CardAttribute, size: float, margin: tuple[float, float]
) -> None:
    name = f"{attr.name.lower()}.png"
    margin = _relative_size(im.size, margin)
    with Image.open(environ.resource_path / "attribute" / name) as icon:
        icon = image.relative_resize(icon, im.size, size)
        im.paste(icon, (im.size[0] - margin[0] - icon.size[0], margin[1]), icon)


def _draw_frame(im: ImageType, rarity: CardRarity) -> None:
    name = f"{rarity.name.lower()}.png"
    with Image.open(environ.resource_path / "frame" / name) as frame:
        frame = frame.resize(im.size)
        im.paste(frame, (0, 0), frame)


def decorate_card_banner(
    im: ImageType,
    info: CardInfo,
    pattern: CardPattern = CardPattern.NORMAL,
    rarity_size: float = 0.05,
    rarity_margin: tuple[float, float] = (0.02, 0.03),
    attr_size: float = 0.05,
    attr_margin: tuple[float, float] = (0.02, 0.03),
) -> ImageType:
    im = im.copy()
    if info.rarity == CardRarity.BIRTHDAY:
        _draw_rarity_birthday(im, rarity_size, rarity_margin)
    else:
        _draw_rarity_normal(im, int(info.rarity), pattern, rarity_size, rarity_margin)
    _draw_attr(im, info.attribute, attr_size, attr_margin)
    _draw_frame(im, info.rarity)
    return im
