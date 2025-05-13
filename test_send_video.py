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
from aiogram.types import (Message, CallbackQuery,
                           InputFile, FSInputFile,
                            MessageEntity, InputMediaDocument,
                            InputMediaPhoto, InputMediaVideo, Document,
                            ReactionTypeEmoji)

logger.add("logs/main_{time}.log",format="{time} - {level} -{file}:{line} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')



async def main():
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    # await bot.delete_webhook(drop_pending_updates=True)
    botName=await bot.get_me()
    logger.info(f'Бот {botName} запущен')
    # await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    await bot.send_message(
        chat_id=400923372,
        text="test",
    )

    file=FSInputFile("videos/Где_роутер_и_щиток.jpg")
    # await bot.send_media_group(
    await bot.send_photo(
        chat_id=400923372,
        photo=file,
        caption="test",
    )
    
    

# При необходимости можно вызвать пример скачивания файла
# asyncio.run(example_yadisk_download())
def test():
    
    url='docx'
    
    from urllib.parse import urlparse, parse_qs
    
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    if 'url' in query_params and 'name' in query_params:
        disk_url = query_params['url'][0]
        file_name = query_params['name'][0]
        if 'Адреса, Инструкции' in disk_url:
            folder = disk_url.split('Адреса, Инструкции/')[-1].split('/')[0]
            full_path = f"/{folder}/{file_name}"
            print(f"Полный путь до файла: {full_path}")
            return file_name
    
    return None
    
if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    test()
    1/0
    print('[OK]')
    asyncio.run(main())