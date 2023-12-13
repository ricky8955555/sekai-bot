import importlib
import inspect
import os
from pathlib import Path
from types import ModuleType

from aiogram import Router


class ModuleManager:
    _router: Router
    _modules: set[ModuleType]

    @property
    def root_router(self) -> Router:
        return self._router

    @property
    def loaded_modules(self) -> set[ModuleType]:
        return set(self._modules)

    def __init__(self, root_router: Router) -> None:
        self._router = root_router
        self._modules = set()

    @staticmethod
    def _collect_modules(path: str | Path) -> set[str]:
        # it only collects modules in the root of specific path located in current working path.
        path = Path(path).absolute().relative_to(Path(os.getcwd()))
        assert path.is_dir(), "attempt to collect modules from a non-directory path."
        modules = [
            item.with_suffix("").as_posix().replace("/", ".")
            for item in Path(path).iterdir()
            if (item.is_file() or (item / "__init__.py").exists()) and not item.stem.startswith("_")
        ]
        modules_set = set(modules)
        assert len(modules_set) == len(modules), "duplicated modules were detected."
        return modules_set

    def import_modules(self, *modules: str) -> None:
        for module in modules:
            self._modules.add(importlib.import_module(module))

    def import_modules_from(self, path: str | Path) -> None:
        modules = self._collect_modules(path)
        self.import_modules(*modules)

    def create_router(self, name: str | None = None) -> Router:
        if not name:
            caller = inspect.stack()[1]
            module = inspect.getmodule(caller.frame)
            name = module.__name__ if module else None
        router = Router(name=name)
        return self._router.include_router(router)
