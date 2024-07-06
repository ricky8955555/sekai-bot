from PIL.Image import Image as ImageType


def crop_to_fit_ratio(im: ImageType, ratio: float) -> ImageType:
    if im.size[0] / im.size[1] > ratio:
        # width bigger than expected
        width = int(im.size[1] * ratio)
        left = int((im.size[1] - width) / 2)
        return im.crop((left, 0, width, im.size[1]))
    else:
        # height bigger than expected
        height = int(im.size[0] / ratio)
        top = int((im.size[1] - height) / 2)
        return im.crop((0, top, im.size[0], height))


def relative_resize(icon: ImageType, size: tuple[int, int], factor: float) -> ImageType:
    factor = (min(size) * factor) / max(icon.size)
    target = tuple(map(int, map(factor.__mul__, icon.size)))
    return icon.resize(target)
