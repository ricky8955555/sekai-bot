import asyncio

from aiogram import Bot, Dispatcher

from sekai.bot import context, environ
from sekai.bot.module import ModuleManager


async def main():
    bot = Bot(context.bot_config.token)
    dispatcher = Dispatcher()
    context.module_manager = ModuleManager(dispatcher)
    context.module_manager.import_modules_from(environ.module_path)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
