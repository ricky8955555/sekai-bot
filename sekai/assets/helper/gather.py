import contextlib
from inspect import isawaitable
from typing import Any, Callable

from sekai.assets import AssetProvider
from sekai.assets.exc import AssetNotFound


class AssetGatherer(AssetProvider):
    def _wrap(self, methods: list[Callable[..., Any]]):
        async def _wrapper(*args: Any, **kwargs: Any) -> Any:
            for method in methods:
                with contextlib.suppress(AssetNotFound, NotImplementedError):
                    result = method(*args, **kwargs)
                    return await result if isawaitable(result) else result
            raise AssetNotFound

        return _wrapper

    def _wrap_methods(self, providers: list[AssetProvider]) -> None:
        for method in AssetProvider.__abstractmethods__:
            methods = [getattr(ins, method) for ins in providers]
            wrapped_method = self._wrap(methods)
            setattr(self, method, wrapped_method)

    def __new__(cls, providers: list[AssetProvider]) -> "AssetProvider":
        cls.__abstractmethods__ = frozenset()
        obj = super().__new__(cls)
        obj._wrap_methods(providers)
        return obj
