import asyncio
from aiogram import types, F, Router, html, Bot
from aiogram.types import (Message, CallbackQuery,
                           InputFile, FSInputFile,
                            MessageEntity, InputMediaDocument,
                            InputMediaPhoto, InputMediaVideo, Document,
                            ReactionTypeEmoji)
from aiogram.filters import Command, StateFilter,ChatMemberUpdatedFilter
from pprint import pprint
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import re
from dotenv import load_dotenv
import os
from loguru import logger
from workGS import Sheet
from workKeyboard import get_keyboard

logger.add("logs/handlers_{time}.log",format="{time} - {level} -{file}:{line} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
SHEET_URL=os.getenv('SHEET_URL')
router = Router()

bot = Bot(token=TOKEN)

s=Sheet(jsonPath='beget-test-456816-c17398de9334.json',
        sheetName='BeGuest_база_квартир'
        ,workSheetName='Лист1')

# Словарь для хранения информации о комнатах по chat_id
user_rooms = {}

# infoRoom=s.get_prepare_info_room('8 марта 204д - 116 (16 этаж)')


@router.message(Command('start'))
async def start(message: Message):
    await message.answer(f'Пришлите название квартиры из списка квартир в таблице {SHEET_URL}')

@router.message(F.text)
async def get_info_room(message: Message):
    infoRoom=s.get_prepare_info_room(message.text)
    logger.info(f'infoRoom: {infoRoom}')
    keyboard=get_keyboard(infoRoom)
    
    # Сохраняем данные о комнате для пользователя
    user_rooms[message.from_user.id] = infoRoom
    
    await message.answer('Информация о квартире', reply_markup=keyboard)

@router.callback_query(F.data.startswith("show_"))
async def show_submenu(callback: CallbackQuery):
    # Получаем ключ из колбэка
    # logger.info(f'callback: {callback}')
    key = callback.data.replace("show_", "")
    # logger.info(f'Получен ключ: {key}')
    
    # Получаем данные о комнате для этого пользователя
    user_data = user_rooms.get(callback.from_user.id)
    if not user_data:
        await callback.answer("Информация устарела, начните заново")
        return
    
    # logger.info(f'Данные пользователя: {user_data}')
    # logger.info(f'Данные для ключа {key}: {user_data.get(key)}')
    
    # Создаем клавиатуру для конкретного ключа
    keyboard = get_keyboard(user_data, filter_key=key)
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "back")
async def back_to_main(callback: CallbackQuery):
    # Получаем данные о комнате для этого пользователя
    # logger.info(f'callback: {callback}')
    user_data = user_rooms.get(callback.from_user.id)
    if not user_data:
        await callback.answer("Информация устарела, начните заново")
        return
    
    # Создаем основную клавиатуру
    keyboard = get_keyboard(user_data)
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()




