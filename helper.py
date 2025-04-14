from pprint import pprint
from urllib.parse import quote,unquote
from test import encode_yandex_url

def get_path_to_file_instruction(url, returnIsUrl=False)->list[str]:
    """
    Получает путь к файлу из URL
    in: https://docs.yandex.ru/docs/view?url=ya-disk-public%3A%2F%2FED7Np%2FfsnHmFPEp0%2BkOUdjFQQAs9J%2FKvkBTN4qWxuSujpRlCytnY3t95176lSoayq%2FJ6bpmRyOJonT3VoXnDag%3D%3D%3A%2FАдреса%2C%20Инструкции%2FМалевич(Трамвайный%20пер.%202%20кор.7-237).docx&name=Малевич(Трамвайный%20пер.%202%20кор.7-237).docx 
    out:Адреса, Инструкции/8 марта 204Д - 116 (16) .docx
    returnIsUrl:True - возвращает URL без кодировки
    https://docs.yandex.ru/docs/view?url=ya-disk-public://ED7Np/fsnHmFPEp0+kOUdjFQQAs9J/KvkBTN4qWxuSujpRlCytnY3t95176lSoayq/J6bpmRyOJonT3VoXnDag==:/Адреса, Инструкции/Малевич(Трамвайный пер. 2 кор.7-237).docx&name=Малевич(Трамвайный пер. 2 кор.7-237).docx
    """
    urls=url.split(',')
    # Разбиваем URL на части по параметрам
    prepare_urls=[]
    for url in urls:
        if returnIsUrl:
            encoded_url=encode_yandex_url(url)
            # print(encoded_url)
            prepare_urls.append(encoded_url)
            continue
            
            
            
        # Логика для returnIsUrl=False (существующая логика)
        url_parts = url.split('?')[1].split('&')
        
        # Получаем значение параметра url
        file_url = ''
        for part in url_parts:
            if part.startswith('url='):
                file_url = part.replace('url=', '')
                break
        
        # Декодируем URL-encoded строку
        decoded_url = file_url.replace('%20', ' ').replace('%2F', '/').replace('%3A', ':').replace('%2C', ',')
        
        # Извлекаем путь после последнего двоеточия
        path = decoded_url.split(':')[-1]
        prepare_urls.append(path)
        
    # pprint(prepare_urls)
    return prepare_urls

def get_path_to_file_info(url, returnIsUrl=False)->list[str]:
    """
    Получает путь к файлу из URL
    in: https://disk.yandex.ru/d/GdBBbAgu5NFSFQ/ИНФО%20ПО%20КВАРТИРАМ/8%20марта%20204д%20-%20116%20(16%20этаж)/Где%20мусорка.mov
    out:/ИНФО ПО КВАРТИРАМ/8 марта 204д - 116 (16 этаж)/Где мусорка.mov
    returnIsUrl:True - возвращает URL без кодировки
    'https://disk.yandex.ru/d/GdBBbAgu5NFSFQ/ИНФО ПО КВАРТИРАМ/8 марта 204д - 116 (16 этаж)/Где мусорка.mov'
    """
    urls=url.split(',')
    prepare_urls=[]
    for url in urls:
        if returnIsUrl:
            decoded_url = url.replace('%20', ' ').replace('%2F', '/').replace('%2C', ',')
            # print(decoded_url)
            encoded_url=prepare_url_encoding(decoded_url)
            # print(encoded_url)
            prepare_urls.append(encoded_url)
            continue
            
        path = url.split('/d/')[1]
        path = '/' + '/'.join(path.split('/')[1:])
        decoded_path = path.replace('%20', ' ').replace('%2F', '/').replace('%2C', ',')
        # print(decoded_path)
        prepare_urls.append(decoded_path)
    
    # print(prepare_urls)
    return prepare_urls

def prepare_url_encoding(url):
    """
    Преобразует декодированный URL в корректно закодированный URL
    in: https://disk.yandex.ru/d/GdBBbAgu5NFSFQ/ИНФО ПО КВАРТИРАМ/Готвальда 24 корп.4 -103/Где мусорка.mov
    out: https://disk.yandex.ru/d/GdBBbAgu5NFSFQ/%D0%98%D0%9D%D0%A4%D0%9E%20%D0%9F%D0%9E%20%D0%9A%D0%92%D0%90%D0%A0%D0%A2%D0%98%D0%A0%D0%90%D0%9C/%D0%93%D0%BE%D1%82%D0%B2%D0%B0%D0%BB%D1%8C%D0%B4%D0%B0%2024%20%D0%BA%D0%BE%D1%80%D0%BF.4%20-103/%D0%93%D0%B4%D0%B5%20%D0%BC%D1%83%D1%81%D0%BE%D1%80%D0%BA%D0%B0.mov
    """
    # Сначала декодируем URL если он уже содержит кодированные части
    decoded_url = url.replace('%20', ' ').replace('%2F', '/').replace('%3A', ':').replace('%2C', ',').replace('%3D', '=')
    
    # Разделяем URL на части
    parts = decoded_url.split('/')
    
    # Кодируем только части пути после домена (первые 3 части оставляем без кодирования)
    encoded_parts = []
    for i, part in enumerate(parts):
        if i < 3:
            encoded_parts.append(part)
        else:
            encoded_parts.append(quote(part, safe=''))
    
    # Собираем URL обратно
    encoded_url = '/'.join(encoded_parts)
    
    return encoded_url




def extract_filenames(urls):
    filenames = []
    for url in urls:
        # Извлекаем часть после последнего '/'
        encoded_filename = url.split('/')[-1]
        # Декодируем URL-спецсимволы (например, %20 -> пробел)
        decoded_filename = unquote(encoded_filename)
        # Разделяем имя файла и расширение по последней точке
        if '.' in decoded_filename:
            name_parts = decoded_filename.rsplit('.', 1)
            filename_without_extension = name_parts[0]
        else:
            filename_without_extension = decoded_filename
        filenames.append(filename_without_extension)
    return filenames


if __name__ == '__main__':
    url='https://docs.yandex.ru/docs/view?url=ya-disk-public%3A%2F%2FED72Np%2FfsnHmFP33Ep0%2BkOUdjFQQAs9J%2FKvkBTN4qWxuSujpRlCytnY3t952176lSoayq%2FJ6bpmRyOJonT3VoXnDag%3D%3D%3A%2FАдреса%2C%20Инструкции%2FМалевич(Трамвайный%20пер.%202%20кор.7-237).docx&name=Малевич(Трамвайный%20пер.%202%20кор.7-237).docx'
    get_path_to_file_instruction(url, returnIsUrl=True)
    url="https://disk.yandex.ru/d/GdBBbAgu7АFSFQ/ИНФО%20ПО%20КВАРТИРАМ/Азина%2022%20корп.2%20-198%20(11%20этаж)/Как%20выглядит%20квартира.mov,https://disk.yandex.ru/d/GdBBbAgu7АFSFQ/ИНФО%20ПО%20КВАРТИРАМ/Азина%2022%20корп.2%20-198%20(11%20этаж)/Номер%20охраны.JPG,https://disk.yandex.ru/d/GdBBbAgu7АFSFQ/ИНФО%20ПО%20КВАРТИРАМ/Азина%2022%20корп.2%20-198%20(11%20этаж)/Про%20ТВ%20в%20спальне.JPG"
    get_path_to_file_info(url, returnIsUrl=True)