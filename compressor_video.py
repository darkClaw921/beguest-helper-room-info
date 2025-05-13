import os
import traceback
import ffmpeg
import pathlib
import shutil
from loguru import logger

logger.add('logs/compressor_video.log', level='DEBUG')

def compress_video(input_path, target_size_mb=20, max_attempts=3):
    """
    Сжимает видео до указанного размера (по умолчанию 50 МБ)
    
    Args:
        input_path: путь к исходному видео файлу
        target_size_mb: целевой размер файла в МБ
        max_attempts: максимальное количество попыток сжатия
    
    Returns:
        строка: путь к сжатому файлу
    """
    input_path = pathlib.Path(input_path)
    # save_path = pathlib.Path('videos/compressed/')
    # Проверка существования исходного файла
    if not input_path.exists():
        logger.error(f"Ошибка: файл {input_path} не найден")
        return None
    
    # Создаем имя выходного файла с суффиксом "_low"
    # output_path = input_path.parent / f"{input_path.stem}_telegram{input_path.suffix}"
    
    output_path = f"videos/compressed/{input_path.stem}_telegram{input_path.suffix}"
    # output_path = save_path / output_path
    print(output_path)
    # Целевой размер в килобайтах
    target_size_kb = target_size_mb * 1024
    
    # Минимальные битрейты для обеспечения качества
    min_audio_bitrate = 32000  # 32 кбит/с
    max_audio_bitrate = 256000  # 256 кбит/с
    min_video_bitrate = 100000  # 100 кбит/с
    
    # Коэффициент для уменьшения битрейта при повторных попытках
    bitrate_reduction_factor = 0.7
    
    attempt = 0
    final_output_path = None
    
    while attempt < max_attempts:
        attempt += 1
        
        try:
            # Получаем информацию о видеофайле
            input_path_str = str('videos/'+input_path.stem+input_path.suffix)
            logger.debug(f"Получаем информацию о видеофайле: {input_path_str}")
            probe = ffmpeg.probe(input_path_str)
            
            # Длительность видео в секундах
            duration = float(probe['format']['duration'])
            
            # Определяем аудио битрейт (если аудио присутствует)
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            if audio_stream and 'bit_rate' in audio_stream:
                audio_bitrate = float(audio_stream['bit_rate'])
            else:
                # Если аудио нет или битрейт не указан, используем значение по умолчанию
                audio_bitrate = min_audio_bitrate
            
            # Рассчитываем целевой общий битрейт с учетом попытки
            target_total_bitrate = (target_size_kb * 8 * 1024) / (duration * 1.073741824)
            if attempt > 1:
                target_total_bitrate *= bitrate_reduction_factor ** (attempt - 1)
            
            # Рассчитываем битрейт для аудио
            if 10 * audio_bitrate > target_total_bitrate:
                audio_bitrate = target_total_bitrate / 10
                if audio_bitrate < min_audio_bitrate:
                    audio_bitrate = min_audio_bitrate
                elif audio_bitrate > max_audio_bitrate:
                    audio_bitrate = max_audio_bitrate
            
            # Рассчитываем битрейт для видео (оставшаяся часть)
            video_bitrate = target_total_bitrate - audio_bitrate
            
            # Проверка на слишком низкий битрейт
            if video_bitrate < min_video_bitrate:
                logger.warning(f"Предупреждение: целевой размер {target_size_mb} МБ слишком мал для качественного сжатия.")
                video_bitrate = min_video_bitrate
            
            logger.debug(f"Попытка {attempt}: сжатие видео с битрейтом видео {int(video_bitrate/1000)} Кбит/с")
            
            # Сжатие видео с двухпроходным кодированием для лучшего качества
            i = ffmpeg.input(str(input_path))
            
            # Первый проход (анализируем видео)
            ffmpeg.output(
                i, os.devnull,
                **{
                    'c:v': 'libx264',
                    'b:v': video_bitrate,
                    'pass': 1,
                    'f': 'mp4'
                }
            ).overwrite_output().run(quiet=True)
            
            # Второй проход (кодируем видео с целевым битрейтом)
            ffmpeg.output(
                i, str(output_path),
                **{
                    'c:v': 'libx264',
                    'b:v': video_bitrate,
                    'pass': 2,
                    'c:a': 'aac',
                    'b:a': audio_bitrate
                }
            ).overwrite_output().run(quiet=True)
            
            # Очистка временных файлов от двухпроходного кодирования
            temp_files = ["ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            # Проверяем размер полученного файла
            output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.debug(f"Размер сжатого файла: {output_size_mb:.2f} МБ")
            
            if output_size_mb <= target_size_mb:
                final_output_path = str(output_path)
                logger.debug(f"Видео успешно сжато до {output_size_mb:.2f} МБ и сохранено как {output_path}")
                break
            else:
                logger.debug(f"Файл всё еще превышает целевой размер ({output_size_mb:.2f} МБ > {target_size_mb} МБ). Повторное сжатие...")
                
        except Exception as e:
            logger.error(f"Ошибка при сжатии видео (попытка {attempt}): {traceback.format_exc()}")
            if attempt == max_attempts:
                return None
    
    return final_output_path

# Пример использования
if __name__ == "__main__":
    # compress_video("квартира2.mov")
    
    # compress_video("videos/Где мусорка.mov")
    compress_video("videos/Где_мусорка.mov")