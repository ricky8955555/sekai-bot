import contextlib


def shorten(text: str, length: int, placeholder: str = "..."):
    if len(text) <= length:
        return text
    with contextlib.suppress(ValueError):
        return text[: text.rindex("\n\n", 0, length)] + (f"\n{placeholder}" if placeholder else "")
    with contextlib.suppress(ValueError):
        return text[: text.rindex("\n", 0, length)] + (f"\n{placeholder}" if placeholder else "")
    return text[:length] + placeholder
