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
    
    

if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    print('[OK]')
    asyncio.run(main())