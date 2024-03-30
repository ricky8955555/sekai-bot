import asyncio

from aiogram import Bot, Dispatcher

from sekai.bot import context, environ
from sekai.bot.module import ModuleManager


async def main():
    context.bot = bot = Bot(context.bot_config.token)
    dispatcher = Dispatcher()

    context.module_manager = module_manager = ModuleManager(dispatcher)
    module_manager.import_modules_from(environ.module_path)

    context.master_api.run_cache_task()

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
