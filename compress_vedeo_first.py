from yadisk_downloader import YandexDiskDownloader
from pprint import pprint
from loguru import logger
from compressor_video import compress_video
import os
from tqdm import tqdm

logger.add('logs/compress_vedeo_first.log', level='INFO')
downloader = YandexDiskDownloader()
MAIN_PATH='disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам'


if __name__ == "__main__":
    
    folders=downloader.get_all_items_in_folder('disk:/✅ИНСТРУКЦИИ и ИНФО по крвартирам/ИНФО ПО КВАРТИРАМ/')
    pprint(folders)
    logger.debug(f'количество папок: {len(folders)}')
    folders=folders[20:]
    # folders=folders[0]
    # pprint(folders)
    # 1/0

    for folder in tqdm(folders):
        path=folder.path
        logger.debug(f'патч до папки: {path}')
        files=downloader.get_all_items_in_folder(path)
        for file in tqdm(files):
            if file.type == 'file':
                logger.debug(f'файл: {file.name}')
                logger.debug(f'размер: {file.size}')
                logger.debug(f'путь: {file.path}')

                video_formats=['mov','mp4','avi','mkv']
                
                if file.name.endswith(tuple(video_formats)):
                    file_name=file.name.replace(' ','_')
                    compressed_file_name=file_name.replace('.','_telegram.')
                    logger.debug(f'сжимаем файл: {file_name}')

                    downloader.download_file(file.path, f'videos/{file_name}')
                    compressed_file_path=compress_video(f'videos/{file_name}')
                    
                    logger.debug(f'выгружаем файл: {path}/{compressed_file_name}')
                    downloader.upload_file(compressed_file_path, path+f'/{compressed_file_name}')
                    
                    logger.debug(f'удаляем файлы: {path}/{file_name}')
                    os.remove(f'videos/{file_name}')
                    os.remove(compressed_file_path)