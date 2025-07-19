from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from helper import get_path_to_file_info, get_path_to_file_instruction, extract_filenames
import os
import hashlib

# Словарь для хранения соответствий между ID и полным URL
url_mapping = {}
# Базовый URL Яндекс.Диска
YANDEX_BASE_URL = "https://disk.yandex.ru/d/GdBBbAgu5NFSFQ/ИНФО%20ПО%20КВАРТИРАМ"

def get_url_id(url):
    """
    Создает уникальный короткий ID для URL
    """
    # Используем часть хеша от URL как идентификатор
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    # Сохраняем соответствие ID и URL
    url_mapping[url_hash] = url
    return url_hash

@logger.catch
def get_keyboard(items: dict, filter_key=None):
    """
    Создает клавиатуру с кнопками для каждого элемента словаря
    Если filter_key указан, создаст клавиатуру только с элементами для этого ключа
    """
    
    builder = InlineKeyboardBuilder()
    
    # Видеоформаты, которые будем скачивать
    video_formats = ['.mov', '.mp4', '.avi', '.mkv', '.MOV', '.MP4', '.AVI', '.MKV']
    # Форматы изображений, для которых тоже используем скачивание
    image_formats = ['.jpg', '.jpeg', '.png', '.heic', '.JPG', '.JPEG', '.PNG', '.HEIC']

    docs_formats = ['.docx', '.doc', '.xlsx', '.xls', '.XLSX', '.XLS']
    
    if filter_key:
        # Создаем клавиатуру только для конкретного ключа
        logger.info(f'Создание подменю для ключа: {filter_key}')
        values = items.get(filter_key, [])
        logger.info(f'Полученные значения: {values}')
        
        if filter_key == 'Инструкция по заселению':
            values = get_path_to_file_instruction(values, returnIsUrl=True)
        else:
            values = get_path_to_file_info(values, returnIsUrl=True)
        
        logger.info(f'Обработанные значения: {values}')
        
        if isinstance(values, list) and len(values) > 0:
            for i, value in enumerate(values):
                # Проверяем, является ли значение относительным путем
                if value.startswith('/') and '://' not in value:
                    # Для относительных путей извлекаем имя файла
                    file_name = os.path.basename(value)
                    nameFile = os.path.splitext(file_name)[0]
                else:
                    # Для полных URL используем существующую функцию
                    nameFile = extract_filenames([value])[0]
                
                if len(nameFile) > 30:
                    nameFile = nameFile[:30] + '...'
                
                # Определяем расширение файла
                file_ext = os.path.splitext(value)[1].lower()
                # Обрабатываем видео и изображения через download_
                if any(ext.lower() == file_ext for ext in video_formats + image_formats + docs_formats):
                    # Сохраняем оригинальный путь, даже если относительный
                    url_id = get_url_id(value)
                    builder.button(text=f"📎 {nameFile}", callback_data=f"download_{url_id}")
                else:
                    # Для остальных файлов
                    if value.startswith('/') and '://' not in value:
                        # Если относительный путь, добавляем базовый URL
                        full_url = f"{YANDEX_BASE_URL}{value}"
                        builder.button(text=f"{nameFile}", url=full_url)
                    else:
                        # Для полных URL оставляем как есть
                        builder.button(text=f"{nameFile}", url=value)
            
            # Добавляем кнопку "Назад"
            builder.button(text="← Назад", callback_data=f"back")
        elif isinstance(values, str):
            # Если только одно значение в виде строки
            file_ext = os.path.splitext(values)[1].lower()
            if any(ext.lower() == file_ext for ext in video_formats + image_formats + docs_formats):
                # Для видео и изображений используем download_
                url_id = get_url_id(values)
                builder.button(text=f"📎 {filter_key}", callback_data=f"download_{url_id}")
            else:
                # Для остальных файлов
                if values.startswith('/') and '://' not in values:
                    # Если относительный путь, добавляем базовый URL
                    full_url = f"{YANDEX_BASE_URL}{values}"
                    builder.button(text=filter_key, url=full_url)
                else:
                    # Для полных URL оставляем как есть
                    builder.button(text=filter_key, url=values)
            builder.button(text="← Назад", callback_data=f"back")
        builder.adjust(1)
        return builder.as_markup()
    
    # Основная клавиатура
    for key, value in items.items():
        if key == 'Квартира' or value is None:
            continue

        if key == 'Инструкция по заселению':
            processed_value = get_path_to_file_instruction(value, returnIsUrl=True)
        else:
            
            processed_value = get_path_to_file_info(value, returnIsUrl=True)
        
        if len(key) > 30:
            key = key[:30] + '...'
        
        # Проверяем тип processed_value
        if isinstance(processed_value, list):
            if len(processed_value) > 1:
                # Если несколько значений, создаем кнопку с колбэком
                builder.button(text=f"{key} ({len(processed_value)})", callback_data=f"show_{key}")
            elif len(processed_value) == 1:
                # Если одно значение, проверяем тип файла
                file_ext = os.path.splitext(processed_value[0])[1].lower()
                if any(ext.lower() == file_ext for ext in video_formats + image_formats + docs_formats):
                    # Для видео и изображений используем download_
                    url_id = get_url_id(processed_value[0])
                    builder.button(text=f"📎 {key}", callback_data=f"download_{url_id}")
                else:
                    # Для остальных файлов
                    if processed_value[0].startswith('/') and '://' not in processed_value[0]:
                        # Если относительный путь, добавляем базовый URL
                        full_url = f"{YANDEX_BASE_URL}{processed_value[0]}"
                        builder.button(text=key, url=full_url)
                    else:
                        # Для полных URL оставляем как есть
                        builder.button(text=key, url=processed_value[0])
        elif processed_value:
            # Если строка, проверяем тип файла
            file_ext = os.path.splitext(processed_value)[1].lower()
            if any(ext.lower() == file_ext for ext in video_formats + image_formats + docs_formats):
                # Для видео и изображений используем download_
                url_id = get_url_id(processed_value)
                builder.button(text=f"📎 {key}", callback_data=f"download_{url_id}")
            else:
                # Для остальных файлов
                if processed_value.startswith('/') and '://' not in processed_value:
                    # Если относительный путь, добавляем базовый URL
                    full_url = f"{YANDEX_BASE_URL}{processed_value}"
                    builder.button(text=key, url=full_url)
                else:
                    # Для полных URL оставляем как есть
                    builder.button(text=key, url=processed_value)
    
    builder.adjust(1)
    return builder.as_markup()
