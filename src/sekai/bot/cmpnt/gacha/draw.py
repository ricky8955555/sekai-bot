import functools
import itertools
from typing import Any, Sequence

from PIL import Image, ImageDraw
from PIL.Image import Image as ImageType

from sekai.bot import environ
from sekai.bot.cmpnt.card.draw import decorate_card_banner
from sekai.bot.utils import image
from sekai.core.models.card import CardInfo


def _draw_polka_dots(
    im: ImageType,
    radius: tuple[int, int] = (1, 1),
    margin: tuple[float, float] = (1, 1),
    fill: tuple[int, int, int, int] = (255, 255, 255, 75),
    outline: tuple[int, int, int, int] = (255, 255, 255, 30),
    width: int = 1,
) -> None:
    # create new layer if image already has alpha channel, otherwise compose on the background directly
    has_alpha = im.mode == "RGBA"
    layer = Image.new("RGBA", im.size) if has_alpha else im
    draw = ImageDraw.Draw(layer, "RGBA")

    # image center
    center = ((im.size[0] // 2), (im.size[1] // 2))

    # dot size
    size = ((radius[0] + width) * 2, (radius[1] + width) * 2)

    # calculated margin
    margin = (int(size[0] * margin[0]), int(size[1] * (margin[1] - 1)))

    # size of a cell
    row = size[0] + (margin[0] * 2)
    column = int((size[1] + margin[1]) * 1.5)

    # offset of adjacent line points on horizon
    offset = int(margin[0] * 1.5)

    # dot count
    horizon = (center[0] // row) + 1
    vertical = (center[1] // column) + 1

    # start position
    left = center[0] - (horizon * row) + size[0]
    top = center[1] - (vertical * column) + size[1]

    # combination of all positions
    poses = itertools.product(range(horizon * 2), range(vertical * 2))

    # compose polka dots
    for x, y in poses:
        # dot start position, left (x) and top (y)
        x = left + (x * row)  #
        if y % 2:
            x += offset
        y = top + (y * column)

        # draw the dot
        draw.ellipse((x, y, x + size[0], y + size[1]), fill, outline, width)

    # apply the layer on the image which has alpha channel
    if has_alpha:
        im.alpha_composite(layer)


def draw_result(
    cards: Sequence[tuple[CardInfo, ImageType]],
    background: ImageType | None = None,
    margin: tuple[float, float] = (0.06, 0.4),  # relative to card
    ratio: float = 16 / 9,
    size: float = 0.8,  # relative to width / 5
    polka_dots: bool = True,
    decorate_kwargs: dict[str, Any] | None = None,
) -> ImageType:
    # copy the provided or default background
    if not background:
        with Image.open(environ.resource_path / "gacha" / "result.png") as im:
            background = im.copy()
    else:
        background = background.copy()

    # draw polka dots
    if polka_dots:
        _draw_polka_dots(background)

    assert len(cards) == 10, "the length of 'cards' should be equal to 10."

    width, height = background.size
    assert width > height, "width should be greater than height."

    # card size
    card_width = int((width / 5) * size)
    card_height = int(card_width / ratio)

    # calculated margin
    margin = (int(card_width * margin[0]), int(card_height * margin[1]))

    # start position
    left = int((width / 2) - (card_width * 2.5) - (margin[0] * 2))
    top = int((height / 2) - card_height - (margin[1] / 2))

    # combination of all positions
    poses = itertools.product(range(2), range(5))

    # prepare decorate function
    decorate_kwargs = decorate_kwargs or {}
    decorate_kwargs.setdefault("rarity_size", 0.15)
    decorate_kwargs.setdefault("attr_size", 0.15)
    decorate = functools.partial(decorate_card_banner, **decorate_kwargs)

    # compose cards on background
    for (y, x), (info, card) in zip(poses, cards):
        # make cards the same size
        card = image.crop_to_fit_ratio(card, ratio)
        card = card.resize((card_width, card_height))

        # decorate the card
        card = decorate(card, info)

        # card start position
        box_left = left + (x * (card_width + margin[0]))
        box_top = top + (y * (card_height + margin[1]))

        # paste the card on background
        background.paste(card, (box_left, box_top))

    return background
