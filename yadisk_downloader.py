from yadisk import YaDisk
import os
from dotenv import load_dotenv
from loguru import logger
from urllib.parse import quote, unquote
import asyncio
from typing import Optional, Union, List, Tuple

# Настройка логирования
logger.add("logs/yadisk_downloader_{time}.log", format="{time} - {level} - {file}:{line} - {message}", 
           rotation="100 MB", retention="10 days", level="DEBUG")

load_dotenv()

class YandexDiskDownloader:
    """
    Класс для скачивания файлов с Яндекс.Диска
    """
    def __init__(self, token: Optional[str] = None, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """
        Инициализация клиента Яндекс.Диска
        
        :param token: OAuth-токен Яндекс.Диска. Если None, берется из переменных окружения
        :param app_id: ID приложения. Если None, берется из переменных окружения
        :param app_secret: Секрет приложения. Если None, берется из переменных окружения
        """
        self.token = token or os.getenv('TOKEN_YD')
        self.app_id = app_id or os.getenv('APLICATION_ID')
        self.app_secret = app_secret or os.getenv('APLICATION_SECRET')
        
        if not self.token:
            raise ValueError("Не указан токен Яндекс.Диска. Укажите его в аргументе или в переменной окружения TOKEN_YD")
            
        self.yadisk = YaDisk(self.app_id, self.app_secret, self.token)
        
        if not self.yadisk.check_token():
            raise ValueError("Недействительный токен Яндекс.Диска")
            
        logger.info("Клиент Яндекс.Диска успешно инициализирован")
    
    def download_file(self, file_path: str, save_path: str) -> bool:
        """
        Скачивает файл с Яндекс.Диска
        
        :param file_path: Путь до файла на Яндекс.Диске
        :param save_path: Путь сохранения файла на локальной машине
        :return: True если файл успешно скачан, иначе False
        """
        downloadTrue=False
        try:
            # Убедимся, что директория существует
            # os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            logger.info(f"Скачивание файла '{file_path}' в '{save_path}'")
            
            self.yadisk.download(file_path, save_path)
            
            
            logger.info(f"Файл успешно скачан: {save_path}")
            downloadTrue=True
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла '{file_path}': {e}")
            file_path=file_path.replace('_telegram', '')
            
            downloadTrue=False
        
        
        if not downloadTrue:
            file_path=file_path.replace('_telegram', '')
            try:
                self.yadisk.download(file_path, save_path)
                downloadTrue=True
            except Exception as e:
                logger.error(f"Ошибка при скачивании файла '{file_path}': {e}")
                downloadTrue=False
        return downloadTrue
        
    
    def get_download_link(self, file_path: str) -> str:
        """
        Получает ссылку на скачивание файла
        
        :param file_path: Путь до файла на Яндекс.Диске
        :return: Ссылка на скачивание
        """
        try:
            link = self.yadisk.get_download_link(file_path)
            logger.info(f"Получена ссылка для скачивания файла '{file_path}': {link}")
            return link
        except Exception as e:
            logger.error(f"Ошибка при получении ссылки для файла '{file_path}': {e}")
            return ""
    
    def file_exists(self, file_path: str) -> bool:
        """
        Проверяет существование файла на Яндекс.Диске
        
        :param file_path: Путь до файла на Яндекс.Диске
        :return: True если файл существует, иначе False
        """
        try:
            return self.yadisk.exists(file_path)
        except Exception as e:
            logger.error(f"Ошибка при проверке существования файла '{file_path}': {e}")
            return False
            
    async def download_file_async(self, file_path: str, save_path: str) -> bool:
        """
        Асинхронная версия скачивания файла
        
        :param file_path: Путь до файла на Яндекс.Диске
        :param save_path: Путь сохранения файла на локальной машине
        :return: True если файл успешно скачан, иначе False
        """
        return await asyncio.to_thread(self.download_file, file_path, save_path)
        
    def get_file_metadata(self, file_path: str) -> dict:
        """
        Получает метаданные файла
        
        :param file_path: Путь до файла на Яндекс.Диске
        :return: Словарь с метаданными или пустой словарь в случае ошибки
        """
        try:
            meta = self.yadisk.get_meta(file_path)
            return {
                "name": meta.name,
                "path": meta.path,
                "created": meta.created,
                "modified": meta.modified,
                "size": meta.size,
                "type": meta.type,
                "mime_type": meta.mime_type if hasattr(meta, "mime_type") else None
            }
        except Exception as e:
            logger.error(f"Ошибка при получении метаданных файла '{file_path}': {e}")
            return {}
    def get_files_from_folder(self, folder_path: str) -> list:
        """
        Получает список файлов из указанной папки
        
        :param folder_path: Путь до папки на Яндекс.Диске
        :return: Список файлов
        """
        try:
            files = self.yadisk.get_meta(folder_path).embedded.items
            return [file.name for file in files if file.file is not None]
        except Exception as e:
            logger.error(f"Ошибка при получении списка файлов из папки '{folder_path}': {e}")
            return []
    
    def get_folder_path(self, folder_name: str) -> str:
        """
        Получает путь до папки на Яндекс.Диске по ее имени
        
        :param folder_name: Имя папки
        :return: Путь до папки
        """
        try:
            folder = self.yadisk.get_meta(folder_name)
            return folder.path
        except Exception as e:
            logger.error(f"Ошибка при получении пути до папки '{folder_name}': {e}")
            return ""
    def get_all_items_in_folder(self, folder_path: str) -> list:
        """
        Получает все элементы (файлы и папки) из указанной папки
        
        :param folder_path: Путь до папки на Яндекс.Диске
        :return: Список всех элементов в папке
        """
        try:
            folder = self.yadisk.get_meta(folder_path, limit=1000)
            return folder.embedded.items
        except Exception as e:
            logger.error(f"Ошибка при получении всех элементов в папке '{folder_path}': {e}")
            return []
    
    def upload_file(self, file_path: str, folder_path: str) -> bool:
        """
        Загружает файл на Яндекс.Диск
        
        :param file_path: Путь до файла на локальной машине
        :param folder_path: Путь до папки на Яндекс.Диске
        :return: True если файл успешно загружен, иначе False
        """

        # self.yadisk.upload(file_path, folder_path, timeout=60)
        try:
            self.yadisk.upload(file_path, folder_path, timeout=60)
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла '{file_path}' на Яндекс.Диск: {e}")
            return False

if __name__ == "__main__":
    from pprint import pprint
    # Пример использования
    downloader = YandexDiskDownloader()
    # MAIN_PATH='disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам'
    MAIN_PATH='disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам'
    file_path = f"{MAIN_PATH}/ИНФО ПО КВАРТИРАМ/Фрунзе 31-127/Как включать плиту.mov"
    save_path = "квартира2_low.mov"
    # Проверяем существование файла
    # MAIN_PATH='/'
    # files=downloader.get_folder_path(MAIN_PATH)
    # pprint(files)

    # files=downloader.download_file(file_path,save_path)
    # pprint(files)
    folder_path=f"{MAIN_PATH}/ИНФО ПО КВАРТИРАМ/8 марта 204д - 116 (16 этаж)/2{save_path}"
    print(folder_path)
    result=downloader.upload_file(save_path,folder_path)
    print(result)
    # if downloader.file_exists(file_path):
    #     # Скачиваем файл
    #     result = downloader.download_file(file_path, save_path)
    #     print(f"Скачивание {'успешно' if result else 'не удалось'}")
    # else:
    #     print(f"Файл '{file_path}' не существует на Яндекс.Диске") 