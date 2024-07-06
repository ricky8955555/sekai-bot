import mimetypes

import magic


def complete_filename(name: str, data: bytes) -> str:
    mime = magic.from_buffer(data, True)
    extension = mimetypes.guess_extension(mime)
    if not extension:
        raise ValueError
    return f"{name}{extension}"
