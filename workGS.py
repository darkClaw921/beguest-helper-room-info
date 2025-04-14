import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from loguru import logger
from pprint import pprint


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


    def get_prepare_info_room(self, roomName: str)->dict:
        """Возвращает подготовленную информацию о квартире"""
        rowRoom=self.find_cell(roomName)
        infoRoom=self.get_all_values_row(rowRoom.row)
        return self.prepare_is_valid_info_room(infoRoom)

if __name__ == '__main__':
    s=Sheet(jsonPath='beget-test-456816-c17398de9334.json',
            sheetName='BeGuest_база_квартир'
            ,workSheetName='Лист1')
    
    
    # infoRoom=s.get_cell('B2')
    # infoRoom=s.get_all_values_row(2)
    # infoRoom=s.find_cell('8 марта 204д - 116 (16 этаж)')
    infoRoom=s.get_prepare_info_room('8 марта 204д - 116 (16 этаж)')
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