import asyncio


from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
# import config
from handlers import router

from dotenv import load_dotenv
import os
from loguru import logger
from yadisk_downloader import YandexDiskDownloader

logger.add("logs/main_{time}.log",format="{time} - {level} -{file}:{line} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')



async def main():
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    botName=await bot.get_me()
    logger.info(f'Бот {botName} запущен')
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
    

async def example_yadisk_download():
    """Пример использования модуля для скачивания файлов с Яндекс.Диска"""
    downloader = YandexDiskDownloader()
    file_path = "/ИНФО ПО КВАРТИРАМ/Азина 22 корп.2 -198 (11 этаж)/Как выглядит квартира.mov"
    save_path = "./downloads/квартира.mov"
    
    if downloader.file_exists(file_path):
        logger.info(f"Найден файл на Яндекс.Диске: {file_path}")
        result = await downloader.download_file_async(file_path, save_path)
        logger.info(f"Результат скачивания: {'успешно' if result else 'не удалось'}")
    else:
        logger.warning(f"Файл не найден на Яндекс.Диске: {file_path}")

# При необходимости можно вызвать пример скачивания файла
# asyncio.run(example_yadisk_download())

if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    print('[OK]')
    asyncio.run(main())