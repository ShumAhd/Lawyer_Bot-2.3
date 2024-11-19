import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def start_polling_with_recovery():
    # Увеличиваем таймаут до 60 секунд
    bot = Bot(token=TOKEN, session=AiohttpSession(timeout=60))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    while True:
        try:
            logging.info("Запуск polling...")
            await dp.start_polling(bot)
        except (asyncio.TimeoutError, ConnectionError) as e:
            logging.error(f"Ошибка сети: {e}")
            logging.info("Повторная попытка через 15 секунд...")
            await asyncio.sleep(15)  # Задержка перед повторной попыткой
        except Exception as e:
            logging.error(f"Непредвиденная ошибка: {e}")
            logging.info("Повторная попытка через 15 секунд...")
            await asyncio.sleep(15)  # Задержка перед повторной попыткой
        finally:
            await bot.session.close()

if __name__ == "__main__":
    asyncio.run(start_polling_with_recovery())
