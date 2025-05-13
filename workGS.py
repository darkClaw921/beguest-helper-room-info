import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from loguru import logger
from pprint import pprint
import os
from urllib.parse import unquote, urlparse, urlunparse, parse_qs

MAP_COLUMN={
        'Квартира':0,
        'Где мусорка':1,
        'Где роутер и щиток':2,
        'Как попасть к дому':3,
        'Как включить плиту':4,
        'Как включить ТВ':5,
        'Где счетчики':6,
        'Как включать микроволновку':7,
        'Инструкция по заселению':8,
        'Дополнительная информация':9}
VIDEO_EXTENSIONS = {'.mov', '.mp4', '.avi', '.mkv', '.webm'}
class Sheet():

    @logger.catch
    def __init__(self, jsonPath: str, sheetName: str, workSheetName, servisName: str = None, sheetDealUrl: str = None):

        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']  # что то для чего-то нужно Костыль
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            jsonPath, self.scope)  # Секретынй файл json для доступа к API
        self.client = gspread.authorize(self.creds)
        if sheetDealUrl:
            self.sheet = self.client.open_by_url(sheetDealUrl).worksheet(workSheetName)
        else:
            self.sheet = self.client.open(sheetName).worksheet(
                workSheetName)  # Имя таблицы
        # self.sheet = self.client.open(workSheetName)  # Имя таблицы

    def send_cell(self, position: str, value):
        #self.sheet.update_cell(position, value=value)
        self.sheet.update(position, value)

    def update_cell(self, r, c, value):
        self.sheet.update_cell(int(r), int(c), value)
        # sheet.update_cell(1, 1, "I just wrote to a spreadsheet using Python!")0

    def find_cell(self, value):
        cell = self.sheet.find(value)
        return cell
    def get_all_values_row(self, row: str):
        cell = self.sheet.row_values(row)
        return cell
    def get_cell(self, row: str):
        # A1
        cell = self.sheet.acell(row).value
        return cell

    def get_value_in_column(self, column: int):
        # 3
        cell = self.sheet.col_values(column)
        return cell

    def insert_cell(self,data:list):
        """Записывает в последнуюю пустую строку"""
        nextRow = len(self.sheet.get_all_values()) + 1
        self.sheet.insert_row(data,nextRow, value_input_option='USER_ENTERED')
    
    def get_last_clear_row_for_column(self, column: str='ЛОКАЦИЯ'):
        """Находит последнюю пустую строку в колонке и возвращает ее номер и номер колонки"""
        colLocation=self.find_cell(column).col
        valuesLocation=self.get_value_in_column(colLocation)
        # pprint(valuesLocation)
        lastClearRowLocation=len(valuesLocation)+1

        
        # location_index = header.index("ЛОКАЦИЯ") + 1  # Индекс колонки (начинается с 1)

        return lastClearRowLocation, colLocation
    @logger.catch
    def prepare_is_valid_info_room(self, infoRoom: list)->dict:
        """Возвращает dict с ключами из MAP_COLUMN и значениями из infoRoom"""
        result={}
        
        for key, value in MAP_COLUMN.items():
            try:
                if infoRoom[value] in ['',None,' ']:
                    continue
                else:
                    result[key]=infoRoom[value]
            except IndexError as e:
                # logger.error(f"Ошибка при подготовке информации о квартире: {traceback.format_exc()}")
                continue
       
        return result

    
    # 
    def process_url(self,url):
        # Обработка ссылок на Яндекс.Документы
        if 'docs.yandex.ru/docs/view' in url:
            try:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                
                if 'url' in query_params and 'name' in query_params:
                    disk_url = query_params['url'][0]
                    file_name = query_params['name'][0]
                    
                    # Извлекаем путь к папке из URL
                    if 'Адреса, Инструкции' in disk_url:
                        return f"/{file_name}"
                        # folder = disk_url.split('Адреса, Инструкции/')[-1].split('/')[0]
                        # return f"/{folder}/{file_name}"

                    else:
                        # Если формат другой, просто возвращаем имя файла
                        return f"/{file_name}"
            except Exception as e:
                logger.error(f"Ошибка при обработке Яндекс.Документ URL: {e}")
                return None
        
        # Стандартная обработка URL
        parsed_url = urlparse(url)
        decoded_path = unquote(parsed_url.path)
        split_path = [p for p in decoded_path.split('/') if p]

        try:
            info_index = split_path.index('ИНФО ПО КВАРТИРАМ')
        except ValueError:
            return None

        if len(split_path) < info_index + 2:
            return None

        parts_after_info = split_path[info_index+1:]
        folder = parts_after_info[0]
        file_path = '/'.join(parts_after_info[1:]) if len(parts_after_info) > 1 else ''

        if not file_path:
            return f"/{folder}"

        dir_name, file_name = os.path.split(file_path)
        name_part, ext_part = os.path.splitext(file_name)
        ext = ext_part.lower()

        if ext in VIDEO_EXTENSIONS:
            new_name = f"{name_part.replace(' ', '_')}_telegram{ext}"
        else:
            new_name = file_name

        new_path = os.path.join(dir_name, new_name) if dir_name else new_name
        return f"/{folder}/{new_path}"

    def update_yandex_links(self,data):
        updated_data = {}
        for key, value in data.items():
            if isinstance(value, str) and ('disk.yandex.ru' in value or 'docs.yandex.ru' in value):
                if ',' in value:
                    values=value.split(',')
                    for value in values:
                        processed = self.process_url(value)
                        try:
                            updated_data[key].append(processed)
                        except:
                            updated_data[key]=[processed]
                else:
                    processed = self.process_url(value)
                    updated_data[key] = processed if processed else value
            else:
                updated_data[key] = value
        return updated_data

    def get_prepare_info_room(self, roomName: str)->dict:
        """Возвращает подготовленную информацию о квартире"""
        rowRoom=self.find_cell(roomName)
        infoRoom=self.get_all_values_row(rowRoom.row)
        infoRoom=self.prepare_is_valid_info_room(infoRoom)
        infoRoom=self.update_yandex_links(infoRoom)
        return infoRoom

if __name__ == '__main__':
    s=Sheet(jsonPath='beget-test-456816-c17398de9334.json',
            sheetName='BeGuest_база_квартир'
            ,workSheetName='Лист1')
    
    
    # infoRoom=s.get_cell('B2')
    # infoRoom=s.get_all_values_row(2)
    # infoRoom=s.find_cell('8 марта 204д - 116 (16 этаж)')
    # infoRoom=s.get_prepare_info_room('8 марта 204д - 116 (16 этаж)')
    infoRoom=s.get_prepare_info_room('Надеждинская 26 -213')
    pprint(infoRoom)
    # infoRoom=s.get_all_values_row(rowRoom.row)
    # pprint(infoRoom)
    # infoRoom=s.prepare_is_valid_info_room(infoRoom)
    # pprint(infoRoom)
   

    # # valuesLocation=s.get_value_in_column(colLocation)
    # lastClearRowLocation, colIndex=s.get_last_clear_row_for_column(col)
    # # pprint(valuesLocation)
    # print(lastClearRowLocation)
    # print(colIndex)

    # s.update_cell(lastClearRowLocation, colIndex, 'test')
    # s.update_cell(2, 1, 'Новый')
    pass