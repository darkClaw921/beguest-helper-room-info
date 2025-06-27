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
import os.path
import json
from loguru import logger
import requests
from workGS import Sheet
from workKeyboard import get_keyboard, url_mapping
from workBitrix import find_contact_by_phone, find_deal_by_contact_id, is_deal_close, update_deal_status, update_telegram_id, Deal, is_deal_status
from aiogram.fsm.state import State, StatesGroup
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Dict, Any, Callable, Awaitable
from yadisk_downloader import YandexDiskDownloader
from helper import extract_text_from_docx, convert_heic_to_jpg, send_message_to_manager, send_message_to_manager, send_first_message_to_manager, send_file_message_to_manager
# from dataclasses import dataclass
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
DOMAIN_BITRIX=os.getenv('DOMAIN_BITRIX')
USER_PHONES={
}


mapping_deal_status={
    'C7:PREPARATION': 'Гость заехал',
    'C7:UC_3EBBY1': 'За 15 мин ничего не прислал',
    'C7:PREPAYMENT_INVOICE': 'Проверка оплаты из бота (если гость отправил скрин платежа)',
}

class Form(StatesGroup):
    phone = State()
    apartment = State()

# Функция для проверки регистрации пользователя
async def is_user_registered(user_id: int) -> bool:
    for phone, data in USER_PHONES.items():
        if data.get('telegram_id') == user_id:
            return True
    return False

# Middleware для проверки регистрации пользователя
class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Пропускаем коллбэки и команду /start
        if isinstance(event, CallbackQuery) or (
            isinstance(event, Message) and event.text and event.text.startswith('/start')
        ):
            return await handler(event, data)
        
        # Проверяем регистрацию для обычных сообщений
        if isinstance(event, Message):
            user_id = event.from_user.id
            
            # Проверяем текущее состояние, чтобы не мешать процессу регистрации
            state = data.get('state')
            if state:
                current_state = await state.get_state()
                if current_state in [Form.phone.state, Form.apartment.state]:
                    return await handler(event, data)
            
            # Если пользователь не зарегистрирован и не в процессе регистрации
            if not await is_user_registered(user_id):
                await event.answer('Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.')
                return
        
        return await handler(event, data)

# Регистрируем middleware
router.message.middleware(RegistrationMiddleware())

@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    await state.set_state(Form.phone)
    message_text=f'Пожалуйста введите ваш номер телефона (начиная с 7 без пробелов), который вы указывали при бронировании\nНапример: 79190072351'
    await message.answer(message_text)
    send_first_message_to_manager(message.from_user.id, message_text, str(message.from_user.first_name), str(message.from_user.last_name), str(message.from_user.username))

@router.message(Command('manager'))
async def start(message: Message, state: FSMContext):
    await state.set_state(Form.phone)
    message_text=f'Если у вас возникли вопросы, вы можете [Написать менеджеру WhatsApp](https://api.whatsapp.com/send?phone=79300356988)'
    await message.answer(message_text)
    send_first_message_to_manager(message.from_user.id, message_text, str(message.from_user.first_name), str(message.from_user.last_name), str(message.from_user.username))

@router.message(Form.phone)
async def process_phone(message: Message, state: FSMContext):
    global USER_PHONES
    phone = message.text.strip()
    send_message_to_manager(message.from_user.id, f'🤖 Пользователь ввёл номер телефона: {phone}')
    # Проверка формата телефона
    if not re.match(r'^7\d{10}$', phone):
        message_text='Неверный формат номера. Пожалуйста, введите номер, начинающийся с 7 и состоящий из 11 цифр.\nНапример: 79190072351'
        await message.answer(message_text)
        send_message_to_manager(message.from_user.id, message_text)
        return
    
    # Сохраняем телефон в состоянии
    await state.update_data(phone=phone)
    
    # Проверяем есть ли пользователь в словаре
    if phone not in USER_PHONES:
        # Если нет, то ищем контакт в Битриксе
        contact = await find_contact_by_phone(phone)
        if not contact:
            message_text='Номер не найден в системе. Пожалуйста, проверьте номер или свяжитесь с администратором.'
            await message.answer(message_text)
            send_message_to_manager(message.from_user.id, message_text)
            return
        
        # Находим сделку по ID контакта
        deal = await find_deal_by_contact_id(contact[0]['ID'])
        if not deal:
            message_text='Сделка не найдена. Пожалуйста, свяжитесь с администратором.'
            await message.answer(message_text)
            send_message_to_manager(message.from_user.id, message_text)
            return
        logger.debug(f'deal: {deal}')
        # Добавляем пользователя в словарь
        USER_PHONES[phone] = {
            'telegram_id': message.from_user.id,
            'deal_id': deal[0]['ID'],
            'status': deal[0]['STAGE_ID'],
            'room_name':deal[0][Deal.room_name] # Название квартиры
             
        }
        # message_text=f'Вы успешно зарегистрированы в системе, вам осталось оплатить {deal[0][Deal.ostatoc_payment]} рублей.\n\nПришлите скрин платежа'
#         message_text=f"""Вы успешно зарегистрированы в системе. 

# Остаток оплаты за проживание {deal[0][Deal.ostatoc_payment]} рублей.
# Оплатить можете по реквизитам:
# 2202208183735308 Сбербанк
# Анастасия Андреевна Ч.

# Для подтверждения оплаты пришлите файл или скриншот платежа.

# Для просмотра информации по заселению нажмите на /info"""
        message_text=f"""Вы успешно зарегистрированы в системе. 

Для просмотра информации по заселению нажмите на /info"""
        await bot.send_message(chat_id=message.from_user.id,
                               text=message_text)
        apartments=USER_PHONES[phone]['room_name']
        deal_link=f'https://{DOMAIN_BITRIX}/crm/deal/details/{deal[0]['ID']}/'
        # additional_info=
        
        
        
        chat_room_id=send_message_to_manager(message.from_user.id, message_text, apartments=apartments, deal_link=deal_link)
        try:
            chat_room_id=chat_room_id['data']['chat_id']
        except:
            chat_room_id='None'
        await update_telegram_id(dealID=deal[0]['ID'],telegram_id=message.from_user.id, chat_room_id=chat_room_id)
    else:
        contact = await find_contact_by_phone(phone)
        if not contact:
            message_text='Номер не найден в системе. Пожалуйста, проверьте номер или свяжитесь с администратором.'
            await message.answer(message_text)
            send_message_to_manager(message.from_user.id, message_text)
            return
        
        # Находим сделку по ID контакта
        deal = await find_deal_by_contact_id(contact[0]['ID'])
        if not deal:
            message_text='Сделка не найдена. Пожалуйста, свяжитесь с администратором.'
            await message.answer(message_text)
            send_message_to_manager(message.from_user.id, message_text)
            return
        logger.debug(f'deal: {deal}')
        USER_PHONES[phone]['deal_id']=deal[0]['ID']
        USER_PHONES[phone]['status']=deal[0]['STAGE_ID']
        USER_PHONES[phone]['room_name']=deal[0][Deal.room_name]
        
        #telegram_id оставляем тот же
        message_text=f'Вы уже зарегистрированы в системе.Ваши апартаменты: {USER_PHONES[phone]['room_name']}. Пожалуйста, используйте команду /info для получения информации о квартире.'
        await message.answer(message_text)
        send_message_to_manager(message.from_user.id, message_text)
        

        
    await state.set_state(Form.apartment)
        
    
    # Переходим к вводу названия квартиры
    # await state.set_state(Form.apartment)
    # await message.answer(f'Пришлите название квартиры из списка квартир в таблице {SHEET_URL}')




@router.message(Command('info'))
async def get_info_room(message: Message, state: FSMContext):
    phone=await state.get_data()
    phone=phone['phone']

    send_message_to_manager(message.from_user.id, '🤖 Пользователь запросил информацию о квартире /info')
    # if not await is_deal_status(dealID=USER_PHONES[phone]['deal_id'],status=Deal.Status.prozivaet):
    #     message_text='Ваш платеж пока не проверен администрацией. Пожалуйста, попробуйте позже.\nПосле проверки вы сможете получить доступ к информации о квартире через команду /info'
    #     await message.answer(message_text)
    #     send_message_to_manager(message.from_user.id, message_text)
    #     return
    if not await is_deal_status(dealID=USER_PHONES[phone]['deal_id'],status=Deal.Status.prozivaet):
        infoRoom = s.get_prepare_info_room(USER_PHONES[phone]['room_name'])
        logger.info(f'infoRoom: {infoRoom}')
        #оставляем только ключи Инструкция по заселению и Как попасть к дому
        if not await is_deal_close(dealID=USER_PHONES[phone]['deal_id']):
            try:
                infoRoom = {
                '🗒 Инструкция по заселению': infoRoom['🗒  Инструкция по заселению'],
                '🏠 Как попасть к дому': infoRoom['🏠 Как попасть к дому']
                }
            except:
                infoRoom = {
                '🗒 Инструкция по заселению': infoRoom['🗒  Инструкция по заселению']
                # '🏠 Как попасть к дому': infoRoom['🏠 Как попасть к дому']
                }
            keyboard = get_keyboard(infoRoom)
            message_text="""Информация по заселению
    После подтверждения оплаты вам будет доступна полная информация по проживанию"""
            await message.answer(message_text, reply_markup=keyboard)
            send_message_to_manager(message.from_user.id, message_text)
            send_message_to_manager(message.from_user.id, infoRoom)
            # message_text='Ваш платеж пока не проверен администрацией. Пожалуйста, попробуйте позже.\nПосле проверки вы сможете получить доступ к информации о квартире через команду /info'
            # await message.answer(message_text)
            # send_message_to_manager(message.from_user.id, message_text)
            return
        else:
            message_text='Ваш договор закрыт. Пожалуйста, свяжитесь с администратором.'
            await message.answer(message_text)
            send_message_to_manager(message.from_user.id, message_text)
            return


    infoRoom = s.get_prepare_info_room(USER_PHONES[phone]['room_name'])
    logger.info(f'infoRoom: {infoRoom}')



    keyboard = get_keyboard(infoRoom)
    
    # Сохраняем данные о комнате для пользователя
    user_rooms[message.from_user.id] = infoRoom
    
    # Очищаем состояние
    # await state.clear()
    message_text='Информация о квартире'
    await message.answer(message_text, reply_markup=keyboard)

    send_message_to_manager(message.from_user.id, message_text)
    send_message_to_manager(message.from_user.id, keyboard.to_json())
# Обработчик для файлов и фотографий
@router.message(F.photo | F.document)
async def process_file(message: Message):
    user_id = message.from_user.id
    
    # Находим информацию о пользователе по его ID
    phone = None
    for p, data in USER_PHONES.items():
        if data['telegram_id'] == user_id:
            phone = p
            break
    
    if not phone:
        message_text='Пожалуйста, сначала введите ваш номер телефона с помощью команды /start'
        await message.answer(message_text)
        send_message_to_manager(message.from_user.id, message_text)
        return
    
    # Обновляем статус сделки
    deal_id = USER_PHONES[phone]['deal_id']
    # Сохраняем фото в папку photos
    # pprint(message)
    # filePath = f'files/{phone}.{message.photo[-1].file_extension}'
    if message.photo:
        file_info = await bot.get_file(message.photo[-1].file_id)
        pprint(file_info)
        fileID=message.photo[-1].file_id
        file_extension = file_info.file_path.split('.')[-1]
        # await message.photo[-1].download(filePath)
    elif message.document:
        file_info = await bot.get_file(message.document.file_id)
        pprint(file_info)
        fileID=message.document.file_id
        file_extension = file_info.file_path.split('.')[-1]

    filePath = f'files/{phone}.{file_extension}'
    await bot.download(fileID,filePath)

    await update_deal_status(deal_id, Deal.Status.check_payment,filePath)

    #кодируем файл base64
    import base64
    with open(filePath, 'rb') as file:
        data = file.read()
    data = base64.b64encode(data).decode('utf-8')
    name_file=filePath.split('/')[-1]
    send_file_message_to_manager(message.from_user.id, name_file, data)
    # Обновляем статус в словаре
    USER_PHONES[phone]['status'] = Deal.Status.check_payment
    message_text='Спасибо! Ваш платеж отправлен на проверку. После проверки вы сможете получить доступ к информации по проживанию.'
    await message.answer(message_text)
    send_message_to_manager(message.from_user.id, message_text)
    send_message_to_manager(message.from_user.id, '🤖 Пользователь отправил файл, просмотреть его вы можете в сделке')

@router.callback_query(F.data.startswith("show_"))
async def show_submenu(callback: CallbackQuery):
    # Получаем ключ из колбэка
    # logger.info(f'callback: {callback}')
    key = callback.data.replace("show_", "")
    # logger.info(f'Получен ключ: {key}')
    
    # Получаем данные о комнате для этого пользователя
    user_data = user_rooms.get(callback.from_user.id)
    if not user_data:
        message_text='Информация устарела, начните заново'
        await callback.answer(message_text)
        send_message_to_manager(callback.from_user.id, message_text)
        return
    
    # logger.info(f'Данные пользователя: {user_data}')
    # logger.info(f'Данные для ключа {key}: {user_data.get(key)}')
    
    # Создаем клавиатуру для конкретного ключа
    keyboard = get_keyboard(user_data, filter_key=key)
    send_message_to_manager(callback.from_user.id, keyboard.to_json())
    await callback.message.edit_reply_markup(reply_markup=keyboard)

    await callback.answer()

@router.callback_query(F.data == "back")
async def back_to_main(callback: CallbackQuery):
    # Получаем данные о комнате для этого пользователя
    # logger.info(f'callback: {callback}')
    user_data = user_rooms.get(callback.from_user.id)
    if not user_data:
        message_text='Информация устарела, начните заново'
        await callback.answer(message_text)
        send_message_to_manager(callback.from_user.id, message_text)
        return
    
    # Создаем основную клавиатуру
    keyboard = get_keyboard(user_data)
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    send_message_to_manager(callback.from_user.id, keyboard.to_json())
    await callback.answer()

# Словарь для хранения file_id отправленных файлов
# Структура: {"локальный_путь_к_файлу": "file_id"}
file_id_cache = {}
FILE_CACHE_PATH = "file_id_cache.json"

# Загружаем кеш file_id, если он существует
def load_file_id_cache():
    global file_id_cache
    try:
        if os.path.exists(FILE_CACHE_PATH):
            with open(FILE_CACHE_PATH, 'r', encoding='utf-8') as f:
                file_id_cache = json.load(f)
                logger.info(f"Загружено {len(file_id_cache)} записей из кеша file_id")
    except Exception as e:
        logger.error(f"Ошибка при загрузке кеша file_id: {e}")
        file_id_cache = {}

# Сохраняем кеш file_id на диск
def save_file_id_cache():
    try:
        with open(FILE_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(file_id_cache, f, ensure_ascii=False)
            logger.info(f"Сохранено {len(file_id_cache)} записей в кеш file_id")
    except Exception as e:
        logger.error(f"Ошибка при сохранении кеша file_id: {e}")

# Загружаем кеш при запуске
load_file_id_cache()

@router.callback_query(F.data.startswith("download_"))
async def download_and_send_file(callback: CallbackQuery):
    # Получаем ID из колбэка
    url_id = callback.data.replace("download_", "")
    logger.info(f'Получен ID для скачивания: {url_id}')
    
    # Получаем полный URL или относительный путь из словаря
    file_path = url_mapping.get(url_id)
    if not file_path:
        logger.error(f'Не найден путь для ID: {url_id}')
        message_text='Ошибка: не удалось найти файл. Попробуйте позже. Или попробуйте авторизироваться заново /start'
        await callback.message.answer(message_text)
        send_message_to_manager(callback.from_user.id, message_text)
        await callback.answer()
        return
    
    logger.info(f'Найден путь: {file_path}')
    
    # Проверяем, является ли путь относительным
    is_relative_path = file_path.startswith('/') and '://' not in file_path
    
    # Получаем имя файла из пути
    file_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(file_name)[0]
    file_ext = os.path.splitext(file_name)[1]
    file_caption = file_name_without_ext.replace('_telegram','').replace('_', ' ')
    
    # Определяем тип файла
    video_formats = ['.mov', '.mp4', '.avi', '.mkv', '.MOV', '.MP4', '.AVI', '.MKV']
    image_formats = ['.jpg', '.jpeg', '.png', '.heic', '.gif', '.JPG', '.JPEG', '.PNG', '.HEIC', '.GIF']
    doc_formats = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
    
    # Определяем тип файла
    file_type = 'document'  # По умолчанию файл считаем документом
    if any(file_ext.lower() == ext for ext in video_formats):
        file_type = 'video'
    elif any(file_ext.lower() == ext for ext in image_formats):
        file_type = 'photo'
    
    # Если видео, добавляем суффикс _telegram
    if file_type == 'video' and '_telegram' not in file_name:
        telegram_file_name = f"{file_name_without_ext.replace(' ', '_')}_telegram{file_ext}"
    else:
        telegram_file_name = file_name.replace(' ', '_')
    
    # Получаем имя папки (название квартиры)
    if is_relative_path:
        # Для относительного пути папка - это первый сегмент пути
        path_segments = file_path.strip('/').split('/')
        folder_name = path_segments[0] if len(path_segments) > 1 else "unknown"
    else:
        # Для полного URL извлекаем папку из пути
        parts = file_path.split('/')
        folder_idx = max([i for i, part in enumerate(parts) if 'КВАРТИРАМ' in part], default=-1)
        if folder_idx != -1 and len(parts) > folder_idx + 1:
            folder_name = parts[folder_idx + 1]
        else:
            folder_name = "unknown"
    
    # Создаем локальную директорию для сохранения скачанных файлов
    folder_name = folder_name.replace('%20', ' ')
    os.makedirs(os.path.join("videos", folder_name), exist_ok=True)
    local_file_path = os.path.join("videos", folder_name, telegram_file_name)
    
    # Проверяем, есть ли файл в кеше по file_id
    if local_file_path in file_id_cache:
        cached_file_id = file_id_cache[local_file_path]
        logger.info(f"Найден закешированный file_id: {cached_file_id} для {local_file_path}")
        send_message_to_manager(callback.from_user.id, f'🤖 Пользователь запросил файл {file_caption}')
        try:
            # Отправляем файл по его file_id в зависимости от типа
            await callback.message.answer("Отправляю файл...")
            
            if file_type == 'video':
                await bot.send_video(
                    chat_id=callback.from_user.id,
                    video=cached_file_id,
                    caption=file_caption,
                    width=1080,
                    height=1920,
                )
            elif file_type == 'photo':
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=cached_file_id,
                    caption=file_caption
                )
            else:  # document
                text=extract_text_from_docx(local_file_path)
                print(text)
                await bot.send_message(
                    chat_id=callback.from_user.id,
                    text=text
                )
                # await bot.send_document(
                #     chat_id=callback.from_user.id,
                #     document=cached_file_id,
                #     caption=file_caption
                # )
                
            await callback.answer()
            return
        except Exception as e:
            logger.error(f"Ошибка при отправке закешированного файла: {e}, удаляем из кеша и скачиваем заново")
            # Если произошла ошибка при отправке по file_id, удаляем его из кеша и скачиваем заново
            del file_id_cache[local_file_path]
            save_file_id_cache()
    
    # Проверяем, существует ли файл локально
    if not os.path.isfile(local_file_path):
        await callback.message.answer(f"Скачиваю файл {file_caption}...")
        send_message_to_manager(callback.from_user.id, f'🤖 Пользователь запросил файл {file_caption}')
        try:
            # Инициализируем даунлоадер Яндекс Диска
            downloader = YandexDiskDownloader()
            
            # Формируем правильный путь к файлу на Яндекс Диске
            if '.docx' in file_path:
                yadisk_path = f'disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам/Адреса, Инструкции{file_path}'
            elif is_relative_path:
                # Если путь относительный, добавляем корневой каталог
                yadisk_path = f"disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам/ИНФО ПО КВАРТИРАМ{file_path}"
            else:
                # Если полный URL, извлекаем путь
                if "ИНФО%20ПО%20КВАРТИРАМ" in file_path or "ИНФО ПО КВАРТИРАМ" in file_path:
                    # Путь уже содержит ИНФО ПО КВАРТИРАМ
                    yadisk_path = f"disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам{file_path.split('ИНФО ПО КВАРТИРАМ')[-1]}"
                elif 'Адреса, Инструкции' in file_path:
                    file_path = file_path.replace('Адреса, Инструкции', '')
                    yadisk_path = f'disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам/Адреса, Инструкции/{file_path}' 
                    print(yadisk_path)
                else:
                    # Другой формат пути
                    yadisk_path = file_path
                        


            logger.info(f'Путь к файлу на Яндекс.Диске: {yadisk_path}')
            
            # Скачиваем файл
            success = await downloader.download_file_async(yadisk_path, local_file_path)
            
                # file_path=
            if not success:
                message_text='Не удалось скачать файл. Пожалуйста, попробуйте позже.'
                await callback.message.answer(message_text)
                send_message_to_manager(callback.from_user.id, message_text)
                await callback.answer()
                return
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла: {e}")
            message_text='Произошла ошибка при скачивании. Пожалуйста, попробуйте позже.'
            await callback.message.answer(message_text)
            send_message_to_manager(callback.from_user.id, message_text)
            await callback.answer()
            return
    
    # Отправляем файл пользователю
    try:
        if '.heic' in file_path:
            local_file_path = convert_heic_to_jpg(local_file_path)
        file = FSInputFile(local_file_path)
        sent_message = None
        
        # Отправляем файл в зависимости от его типа
        if file_type == 'video':
            sent_message = await bot.send_video(
                chat_id=callback.from_user.id,
                video=file,
                caption=file_caption,
                width=1080,
                height=1920,
            )
            # Сохраняем file_id видео
            if sent_message and sent_message.video:
                file_id = sent_message.video.file_id
                logger.info(f"Получен file_id видео: {file_id} для {local_file_path}")
                file_id_cache[local_file_path] = file_id
        
        elif file_type == 'photo':
            sent_message = await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=file,
                caption=file_caption
            )
            # Сохраняем file_id фото
            if sent_message and sent_message.photo:
                file_id = sent_message.photo[-1].file_id  # Берем последнее (самое качественное) фото
                logger.info(f"Получен file_id фото: {file_id} для {local_file_path}")
                file_id_cache[local_file_path] = file_id
        
        else:  # document

            text=extract_text_from_docx(local_file_path)
            print(text)
            await bot.send_message(
                chat_id=callback.from_user.id,
                text=text
            )
            # sent_message = await bot.send_document(
            #     chat_id=callback.from_user.id,
            #     document=file.path,
            #     caption=file_caption
            # )

            # Сохраняем file_id документа
            if sent_message and sent_message.document:
                file_id = sent_message.document.file_id
                logger.info(f"Получен file_id документа: {file_id} для {local_file_path}")
                file_id_cache[local_file_path] = file_id
        
        # Сохраняем кеш file_id
        save_file_id_cache()
        
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}")
        message_text='Не удалось отправить файл. Возможно, файл слишком большой. Обратитесь в тех. поддержку'
        await callback.message.answer(message_text)
        send_message_to_manager(callback.from_user.id, message_text)
    
    await callback.answer()

#обробатываем просто сообщение
@router.message()
async def handle_text_message(message: types.Message):
    text='Если у вас есть вопрос, который нужно решить с администратором, для связи вы можете:\n\n- Позвонить по телефону: +79300356988\n- [Написать в WhatsApp](https://api.whatsapp.com/send?phone=79300356988)'
    await message.answer(text)
    send_message_to_manager(message.from_user.id, text)

    send_message_to_manager(message.from_user.id, f'{message.text}')


