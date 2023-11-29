import asyncio
from aiogram import Bot, Dispatcher
from config.config import Config, load_config
from handlers import main_handlers, post_handlers, setting_handlers, zakaz_handlers, other_handlers
from middle import AlbumMiddleware
from aiogram.fsm.storage.memory import MemoryStorage


# Функция конфигурирования и запуска бота
async def main():
    # Инициализируем Redis
    # redis = Redis(host='localhost')
    # Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
    # storage = RedisStorage(redis=redis)
    storage = MemoryStorage()

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot: Bot = Bot(token=config.tg_bot.token,
                   parse_mode='HTML')
    dp: Dispatcher = Dispatcher(storage=storage)

    dp.message.middleware(AlbumMiddleware())

    # Регистриуем роутеры в диспетчере
    dp.include_router(main_handlers.router)
    dp.include_router(post_handlers.router)
    dp.include_router(zakaz_handlers.router)
    dp.include_router(setting_handlers.router)
    dp.include_router(other_handlers.router)
    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())