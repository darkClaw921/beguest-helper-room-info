
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from helper import get_path_to_file_info, get_path_to_file_instruction, extract_filenames

@logger.catch
def get_keyboard(items: dict, filter_key=None):
    """
    Создает клавиатуру с кнопками для каждого элемента словаря
    Если filter_key указан, создаст клавиатуру только с элементами для этого ключа
    """
    
    builder = InlineKeyboardBuilder()
    
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
                nameFile=extract_filenames([value])[0]
                if len(nameFile) > 30:
                    nameFile=nameFile[:30] + '...'
                builder.button(text=f"{nameFile}", url=value)
            
            # Добавляем кнопку "Назад"
            builder.button(text="← Назад", callback_data=f"back")
        elif isinstance(values, str):
            # Если только одно значение в виде строки
            builder.button(text=filter_key, url=values)
            builder.button(text="← Назад", callback_data=f"back")
        builder.adjust(1)
        return builder.as_markup()
    
    # Основная клавиатура
    for key, value in items.items():
        if key == 'Квартира':
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
                # Если одно значение, создаем кнопку с URL
                builder.button(text=key, url=processed_value[0])
        elif processed_value:
            # Если строка, создаем кнопку с URL
            builder.button(text=key, url=processed_value)
    
    builder.adjust(1)
    return builder.as_markup()
