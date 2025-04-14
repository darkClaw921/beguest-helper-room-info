from pprint import pprint
from yadisk import YaDisk
from dotenv import load_dotenv
from tqdm import tqdm
# import postgreWork
import os
load_dotenv()
APLICATION_ID = os.getenv('APLICATION_ID')
APLICATION_SECRET = os.getenv('APLICATION_SECRET')
TOKEN_YD = os.getenv('TOKEN_YD')

from loguru import logger
logger.add("logs/ydWork_{date}.log",format="{time} - {level} -{file}:{line} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")

class YandexDiskManager:
    def __init__(self, APLICATION_ID, APLICATION_SECRET, TOKEN_YD, isTest=True):
        self.yadisk = YaDisk(APLICATION_ID, APLICATION_SECRET, TOKEN_YD)
        
        if isTest:
            self.pathMain='/Производственный отдел/ТЕСТИРОВАНИЕ/'
        else:
            self.pathMain='/Производственный отдел/ПРОЕКТЫ2/'
        # url = self.yadisk.get_code_url()
        # print(url)
        # code=input('Введите код: ')
        # self.yadisk.get_token(code)
        print(self.yadisk.check_token())
  


    def upload_file_from_url(self, urlFolder, urlFile, nameFile) ->None:
        # meta=self.yadisk.get_public_meta(urlFolder)
        # meta.upload_url(urlFile, self.pathMain+meta.name+"/"+nameFile) 
        self.yadisk.upload_url(urlFile, urlFolder+"/"+nameFile) 

    def upload_file_from_local(self, path, folder_path,nameFile) ->None:
        self.yadisk.upload(path, folder_path+"/"+nameFile)

    def create_folder(self, folder_name)->str:
        urlFold=self.yadisk.mkdir(folder_name)
        publick=urlFold.publish()
        publick=urlFold.get_meta()
        

        publickURL=publick.public_url
        logger.info(f'Создана папка {folder_name}')
        return folder_name, publickURL

    
    def get_all_folders(self, publickURL)->list:
        
        folderProject=self.yadisk.get_public_meta(publickURL).name
        allPath=self.pathMain+folderProject+'/'
        print(f'{allPath=}')
        path=allPath
        files=self.yadisk.get_meta(path).embedded.items
        folders=[]
        for file1 in files:
            if file1.file is None:
                pathFile=file1.path.replace('disk:'+path,'')
                folders.append(pathFile)
        pprint(folders)
        return folders 
    
    # получаем все файлы в папке
    def get_all_files(self, folderName)->list:
        # folderProject=self.yadisk.get_public_meta(folderName).name
        allPath=self.pathMain+folderName+''
        # print(f'{allPath=}')
        path=allPath
        files=self.yadisk.get_meta(path).embedded.items
        filesName=[]
        filesHash=[]
        for file1 in files:
            if file1.file is not None:
                hashFile=file1.md5
                pathFile=file1.path.replace('disk:'+path,'')
                filesName.append(pathFile)
                filesHash.append(hashFile)

        # pprint(filesName)
        # pprint(filesHash)
        return filesHash 

    #переносим файл из одной папки в другую 
    def move_file(mainFilePath, secondPath):


        pass

FOLDERS={}




if __name__ =='__main__':
    pass