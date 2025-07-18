import base64
from dataclasses import dataclass
from datetime import datetime, timedelta
from pprint import pprint
from fast_bitrix24 import BitrixAsync
from dotenv import load_dotenv
import time
import asyncio

from tqdm import tqdm
# mapping_deal_status={
#     'C7:PREPARATION': 'Гость заехал',
#     'C7:UC_3EBBY1': 'За 15 мин ничего не прислал',
#     'C7:PREPAYMENT_INVOICE': 'Проверка оплаты из бота (если гость отправил скрин платежа)',
# }
@dataclass
class Deal:
    telegram_id:str='UF_CRM_1747164098729'
    deal_id:str='ID'
    status:str='STAGE_ID'
    room_name: str='UF_CRM_ROOM_TYPE_NAME'
    ostatoc_payment:str='UF_CRM_1715183997779'
    file_payment:str='UF_CRM_1747158628163'
    chat_room:str='UF_CRM_1747245296634'
    class Status:
        guest_zaehal:str='C1:UC_KF562L'
        guest_no_send_payment:str='C1:UC_UPYQD0'
        check_payment:str='C1:UC_8MQAUR'
        prozivaet:str='C1:PREPAYMENT_INVOICE'

NAME_APP='H_'
import os
load_dotenv()

# номер воронки в битриксе

NEED_CATEGORY=1
WEBHOOK=os.getenv('WEBHOOK')
bit = BitrixAsync(WEBHOOK, ssl=False)
print(f'{WEBHOOK=}')
IP_CHAT_ROOM=os.getenv('IP_CHAT_ROOM')
# Работа с Deal
async def get_deal(dealID):
    items={ 
        'ID':dealID,
        'select':['*', 'UF_'],
    }
    deal = await bit.call('crm.deal.get',items=items,raw=True)
    deal=deal['result']
    return deal

async def get_all_userfields_deal()->list:
    items={
        'filter':{
            '>ID':0,
        }
    }
    
    poles=await bit.call('crm.deal.userfield.list',items=items,raw=True)
   
    poles=poles['result']
    # pprint(poles)
    # poles=prepare_userfields_deal_to_postgres(poles)
    # print(poles)
    return poles

async def get_userfields_deal(fieldID)->list:
    items={
        'ID':fieldID,
        
    }
    field=await bit.call('crm.deal.userfield.get',items=items,raw=True)
    field=field['result']
    pprint(field)
    return field

async def get_all_fields_deal()->list:
    items={
        'select':['*', 'UF_'],
    }
    fields=await bit.call('crm.deal.fields',items=items,raw=True)
    fields=fields['result']
    # pprint(fields)
    return fields

def prepare_userfields_deal_to_postgres(fields:list)->list:
    fieldsToPostgres=[]
    for field in fields:
        fieldName=field.get('FIELD_NAME')
        entityID=field.get('ENTITY_ID')
        userTypeID=field.get('USER_TYPE_ID')
        # print(fieldName, entityID, userTypeID)
        
        fieldToPostgres={
            'fieldID':fieldName,
            'entityID':entityID, #Deal
            'fieldType':userTypeID,
            'description':field.get('title'),
        }
        fieldsToPostgres.append(fieldToPostgres)
        
    return fieldsToPostgres

def prepare_fields_deal_to_postgres(fields:list)->list:
    entityID='CRM_DEAL'
    fieldsToPostgres=[]
    for fieldID, meta in fields.items():
        fieldType=meta.get('type')
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta.get('title'),
        })
    return fieldsToPostgres

async def get_all_deal(last_update=None)->list:
    items={
        'FILTER':{
            '>ID':0,
        },
        'SELECT':['*', 'UF_*'],
    }
    if last_update:
        items['FILTER']['>DATE_MODIFY'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    deals = await bit.get_all('crm.deal.list', params=items)
    # deals=await bit.call('crm.deal.list',items=items)
    deals=deals
    return deals

async def get_history_move_deal(last_update=None):
    #https://apidocs.bitrix24.ru/api-reference/crm/crm-stage-history-list.html
    """
    entityTypeId - ID типа сущности
    1 - Lead
    2 - Deal
    5 - Invoice
    """
    items={
        'entityTypeId':'2',
        # 'select':['*', 'UF_*'],
    }
    if last_update:
        items['filter']['>TIMESTAMP_X'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    history=await bit.get_all('crm.stagehistory.list',params=items)
    # history=history
    return history



# Работа с Company
async def get_company(companyID):
    items={
        'ID':companyID,
        'select':['*', 'UF_'],
    }
    company=await bit.call('crm.company.get',items=items,raw=True)
    company=company['result']
    return company

async def get_all_fields_company()->list:
    fields=await bit.call('crm.company.fields',raw=True)
    fields=fields['result']
    return fields

async def get_all_userfields_company()->list:
    items={
        'filter':{
            '>ID':0,
        }
    }
    fields=await bit.call('crm.company.userfield.list',items=items,raw=True)
    fields=fields['result']
    return fields   

async def get_userfields_company(fieldID)->list:
    field=await bit.call('crm.company.userfield.get',items={'ID':fieldID},raw=True)
    field=field['result']
    return field

def prepare_userfields_company_to_postgres(fields:list)->list:
    fieldsToPostgres=[]
    for field in fields:
        fieldName=field.get('FIELD_NAME')
        entityID=field.get('ENTITY_ID')
        userTypeID=field.get('USER_TYPE_ID')
        # print(fieldName, entityID, userTypeID)
        fieldToPostgres={
            'fieldID':fieldName,
            'entityID':entityID,
            'fieldType':userTypeID,
            'description':field.get('title'),
        }
        fieldsToPostgres.append(fieldToPostgres)
    return fieldsToPostgres

def prepare_fields_company_to_postgres(fields:list)->list:
    entityID='CRM_COMPANY'
    fieldsToPostgres=[]
    for fieldID, meta in fields.items():
        fieldType=meta.get('type')
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta.get('title'),
        })
    return fieldsToPostgres

async def get_all_company(last_update=None):
    """Получение всех компаний с фильтрацией по дате обновления"""
    items = {
        'filter': {
            '>ID': 0,
        },
        'select': ['*', 'UF_*'],
    }
    if last_update:
        items['filter']['>DATE_MODIFY'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    companies = await bit.get_all('crm.company.list', params=items)
    companies = companies
    return companies



#Lead
async def get_lead(leadID):
    items={
        'ID':leadID,
        'select':['*', 'UF_*'],
    }
    lead=await bit.call('crm.lead.get',items=items)
    lead=lead['order0000000000']
    return lead 

async def get_all_fields_lead()->list:
    fields=await bit.call('crm.lead.fields',raw=True)
    fields=fields['result']
    return fields

async def get_all_userfields_lead()->list:
    items={
        'filter':{
            '>ID':0,
        }
    }
    fields=await bit.call('crm.lead.userfield.list',items=items,raw=True)
    fields=fields['result']
    return fields

def prepare_userfields_lead_to_postgres(fields:list)->list:
    fieldsToPostgres=[]
    for field in fields:
        fieldName=field.get('FIELD_NAME')
        entityID=field.get('ENTITY_ID')
        userTypeID=field.get('USER_TYPE_ID')
        fieldToPostgres={
            'fieldID':fieldName,
            'entityID':entityID,
            'fieldType':userTypeID,
            'description':field.get('title'),
        }
        fieldsToPostgres.append(fieldToPostgres)
    return fieldsToPostgres

def prepare_fields_lead_to_postgres(fields:list)->list:
    entityID='CRM_LEAD'
    fieldsToPostgres=[]
    for fieldID, meta in fields.items():
        fieldType=meta.get('type')
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta.get('title'),
        })
    return fieldsToPostgres

async def get_all_lead(last_update=None):
    """Получение всех лидов с фильтрацией по дате обновления"""
    items = {
        'filter': {
            '>ID': 0,
        },
        'select': ['*', 'UF_*'],
    }
    if last_update:
        items['filter']['>DATE_MODIFY'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    leads = await bit.get_all('crm.lead.list', params=items)
    leads=leads
    return leads

async def get_history_move_lead()->list[dict]:
    #https://apidocs.bitrix24.ru/api-reference/crm/crm-stage-history-list.html
    """
    entityTypeId - ID типа сущности
    1 - Lead
    2 - Deal
    5 - Invoice
    """
    items={
        'entityTypeId':'1',
    }
    history=await bit.get_all('crm.stagehistory.list',params=items)
    return history





#Contact
async def get_contact(contactID):
    items={
        'ID':contactID,
        'select':['*', 'UF_'],
    }
    contact=await bit.call('crm.contact.get',items=items,raw=True)
    contact=contact['result']
    return contact  

async def get_all_fields_contact()->list:
    fields=await bit.call('crm.contact.fields',raw=True)
    fields=fields['result']
    return fields   

async def get_all_userfields_contact()->list:
    items={
        'filter':{
            '>ID':0,
        }
    }
    fields=await bit.call('crm.contact.userfield.list',items=items,raw=True)
    fields=fields['result']
    return fields

def prepare_userfields_contact_to_postgres(fields:list)->list:
    fieldsToPostgres=[]
    for field in fields:
        fieldName=field.get('FIELD_NAME')
        entityID=field.get('ENTITY_ID')
        userTypeID=field.get('USER_TYPE_ID')
        fieldToPostgres={
            'fieldID':fieldName,
            'entityID':entityID,
            'fieldType':userTypeID,
            'description':field.get('title'),
        }
        fieldsToPostgres.append(fieldToPostgres)
    return fieldsToPostgres

def prepare_fields_contact_to_postgres(fields:list)->list:
    entityID='CRM_CONTACT'
    fieldsToPostgres=[]
    for fieldID, meta in fields.items():
        fieldType=meta.get('type')
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta.get('title'),
        })
    return fieldsToPostgres

async def get_all_contact(last_update=None):
    """Получение всех контактов с фильтрацией по дате обновления"""
    items = {
        'filter': {
            '>ID':0,
            
        },
        'select':['*', 'UF_*'],
    }
    if last_update:
        items['filter']['>DATE_MODIFY'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    contacts = await bit.get_all('crm.contact.list', params=items)
    return contacts




#Task
async def get_task(taskID):
    items={
        'taskId':taskID,
        'select':['*', 'UF_', 'TAGS'],
    }
    task=await bit.call('tasks.task.get',items=items,raw=True)
    task=task['result']['task']
    return task 

async def get_all_fields_task()->list:
    fields=await bit.call('tasks.task.getFields',raw=True)
    fields=fields['result']['fields']
    return fields

def prepare_fields_task_to_postgres(fields:list)->list:
    entityID='CRM_TASK'
    fieldsToPostgres=[]
    for fieldID, meta in fields.items():
        fieldType=meta.get('type')
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta.get('title'),
        })
    fieldsToPostgres.append({
        'fieldID':'UF_CRM_TASK',
        'fieldType':'array',
        'entityID':'CRM_TASK',
        # 'description':,
    })
    return fieldsToPostgres

async def get_all_task(last_update=None):
    """Получение всех задач с фильтрацией по дате обновления"""
    items = {
        'filter': {
            # '>taskId': 0,
        },
        'select': ['*', 'UF_*','TAGS'],
    }
    if last_update:
        items['filter']['>CHANGED_DATE'] = last_update.strftime('%Y-%m-%d')
    
    print(items)
    
    tasks = await bit.get_all('tasks.task.list', params=items)
    # tasksFilter=[]
    # for task in tasks:
    #     dateModify=task.get('changedDate')
    #     dateModify=datetime.strptime(dateModify, '%Y-%m-%d %H:%M:%S')
    #     if dateModify>last_update:
    #         tasksFilter.append(task)
    return tasks



#User
async def get_user(userID)->dict:
    items={
        # 'ID':userID,
        'filter':{
            'ID':userID,
        },
        # 'select':['*', 'UF_'],
    }
    user=await bit.call('user.get',items=items,raw=True)
    user=user['result'][0]
    return user

async def get_all_user()->list:
    items={
        'filter':{
            '>ID':0,
        },
        'ADMIN_MODE':True,
        # 'select':['*', 'UF_*'],
    }
    users=await bit.get_all('user.get',params=items)
    users=users
    return users

async def get_all_user_fields()->list:
    fields=await bit.call('user.fields',raw=True)
    fields=fields['result']
    return fields

async def get_all_user_userfield()->list:
    items={
        'filter':{
            '>ID':0,
        }
    }
    fields=await bit.call('user.userfield.list',items=items,raw=True)
    fields=fields['result']
    return fields

def prepare_user_userfields_to_postgres(fields:list)->list:
    fieldsToPostgres=[]
    for field in fields:
        fieldName=field.get('FIELD_NAME')
        entityID=field.get('ENTITY_ID')
        userTypeID=field.get('USER_TYPE_ID')
        fieldToPostgres={
            'fieldID':fieldName,
            'entityID':entityID,
            'fieldType':userTypeID,
            'description':field.get('title'),
        }
        fieldsToPostgres.append(fieldToPostgres)
    return fieldsToPostgres

def prepare_user_fields_to_postgres(fields:dict)->list:
    entityID='CRM_USER'
    fieldsToPostgres=[]
    pprint
    for fieldID, meta in fields.items():
        fieldType='string'
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta,
        })
    return fieldsToPostgres



#DynamicItem
async def get_all_dynamic_item(last_update=None):
    """Получение всех динамических элементов с фильтрацией по дате обновления"""
    items = {
        'filter': {
            '>ID': 0,
        },
        'select': ['*', 'UF_*'],
    }
    if last_update:
        items['filter']['>date_modify'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    dynamicItem=await bit.call('crm.type.list',items=items,raw=True)
    dynamicItem=dynamicItem['result']['types']
    return dynamicItem
    
async def get_dynamic_item_all_entity(dynamicItemID,last_update=None)->list:
    items={
        'entityTypeId':dynamicItemID,
        'select':['*', 'UF_*'],
    }
    if last_update:
        items['filter']['>date_modify'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
    dynamicItem=await bit.call('crm.item.list',items=items,raw=True)
    dynamicItem=dynamicItem['result']['items']
    return dynamicItem

async def get_dynamic_item_entity(dynamicItemID, entityID)->dict:
    items={
        'entityTypeId':dynamicItemID,
        'id':entityID,
    }
    dynamicItem=await bit.call('crm.item.get',items=items,raw=True)
    dynamicItem=dynamicItem['result']['item']
    return dynamicItem

async def get_dynamic_item_field(dynamicItemID)->dict:
    items={
        'entityTypeId':dynamicItemID,
        'select':['*', 'UF_*'],
    }
    dynamicItem=await bit.call('crm.item.fields',items=items,raw=True)
    dynamicItem=dynamicItem['result']['fields']
    return dynamicItem

def prepare_dynamic_item_field_to_postgres(fields:dict,entityTypeId:int)->list:
    entityID=f'CRM_DYNAMIC_ITEM_{entityTypeId}'
    fieldsToPostgres=[]
    for fieldID, meta in fields.items():
        fieldType=meta.get('type')
        fieldsToPostgres.append({
            'fieldID':fieldID,
            'fieldType':fieldType,
            'entityID':entityID,
            'description':meta.get('title'),
        })
    return fieldsToPostgres

async def get_task_comments_batc(tasks:list):
    """Получение комментариев к задачам"""
    # пакетно получаем комментарии к задачам по 50 задач
    # tasks=await get_all_task()
    
    i=0
    commands={}
    results={}
    for task in tqdm(tasks,desc='Получение комментариев к задачам'):
        i+=1
        if i>48:
            results.update(await bit.call_batch ({
                'halt': 0,
                'cmd': commands
            }))

            commands={}
            i=0
        commands[f'{task["id"]}']=f'task.commentitem.getlist?taskId={task["id"]}'
    return results

async def get_result_task_comments(tasks:list):
    """Получение результатов задач"""
    i=0
    commands={}
    results={}
    for task in tqdm(tasks, 'Получение результатов задач'):
        i+=1
        if i>48:
            results.update(await bit.call_batch ({
                'halt': 0,
                'cmd': commands
            }))

            commands={}
            i=0

        commands[f'{task["id"]}']=f'tasks.task.result.list?taskId={task["id"]}'
    
    # pprint(results)
    return results


#call
async def get_all_call()->list[dict]:
    # items={
    #     'ID':callID,
    #     'select':['*', 'UF_'],
    # }
#     {'CALL_CATEGORY': 'external',
#   'CALL_DURATION': '15',
#   'CALL_FAILED_CODE': '200',
#   'CALL_FAILED_REASON': 'Success call',
#   'CALL_ID': '1977F2315C08E697.1734773622.15063781',
#   'CALL_RECORD_URL': '',
#   'CALL_START_DATE': '2024-12-21T12:33:43+03:00',
#   'CALL_TYPE': '1',
#   'CALL_VOTE': None,
#   'COMMENT': None,
#   'COST': '0.0000',
#   'COST_CURRENCY': 'RUR',
#   'CRM_ACTIVITY_ID': '12',
#   'CRM_ENTITY_ID': '12',
#   'CRM_ENTITY_TYPE': 'CONTACT',
#   'EXTERNAL_CALL_ID': None,
#   'ID': '8',
#   'PHONE_NUMBER': '+',
#   'PORTAL_NUMBER': 'reg130528',
#   'PORTAL_USER_ID': '1',
#   'RECORD_DURATION': None,
#   'RECORD_FILE_ID': None,
#   'REDIAL_ATTEMPT': None,
#   'REST_APP_ID': None,
#   'REST_APP_NAME': None,
#   'SESSION_ID': '3351901428',
#   'TRANSCRIPT_ID': None,
#   'TRANSCRIPT_PENDING': 'N'}
    params={
        'FILTER':{
            '>CALL_START_DATE':'2024-12-12',
        },
    }
    # call=await bit.get_all('voximplant.statistic.get',params=params)
    # call=await bit.call('voximplant.statistic.get',items=params)
    call=await bit.get_all('voximplant.statistic.get',params=params)

    # call=await bit.call('voximplant.statistic.get',raw=True)
    # pprint(call)
    # call=call['result']
    return call


#event
async def get_event(eventID:str)->list:
    items={
        'id':eventID,
    }
    event=await bit.call('calendar.event.getbyid',params=items)
    # event=event['result']
    return event

async def get_all_event_by_user(userID:str=None,last_update=None)->list:
    now=datetime.now()
    if userID is None:
        items={
            'type': 'company_calendar',
            'ownerId': '',   
        }
        print(items)
    else:
        items={
            'type': 'user',
            'ownerId': userID,  
            'from': last_update.strftime('%Y-%m-%d'),
            # 'to': now.strftime('%Y-%m-%d'),
        }
    if last_update:
        # items['filter']['>TIMESTAMP_X'] = last_update.strftime('%Y-%m-%dT%H:%M:%S')
        items['from'] = last_update.strftime('%Y-%m-%d')
    # print(items)
    event=await bit.get_all('calendar.event.get',params=items)
    # event=event['result']
    return event

async def get_all_event(last_update=None)->list:
    users=await get_all_user()
    eventsAll=[]
    print(f'{len(users)=}')
    for i, user in enumerate(users):
        userID=user.get('ID')
        events=await get_all_event_by_user(userID,last_update)
        print(f'{userID=} {len(events)=} {i=}')
        for event in events:
            event.setdefault('bitrix_id',event['ID'])
        
        time.sleep(1.6)
        print(f'добавили {len(events)=} событий')
        eventsAll.extend(events)
        print(f'всего событий {len(eventsAll)=}')
    # print(f'{len(events)=}')
    # events.extend(await get_all_event_by_user(last_update=last_update))
    return eventsAll




#Подразделения
async def get_all_department()->list[dict]:
    # items={
    #     'filter':{
    #         '>ID':0,
    #     },g
    #     'select':['*', 'UF_*'],
    # }
    department=await bit.get_all('department.get')
    
    return department


#Воронки
async def get_all_category(entityTypeId:int=2)->list[dict]:
    """
    entityTypeId=2 - Сделки
    """
    params={
        'entityTypeId':entityTypeId
    }
    status=await bit.get_all('crm.category.list',params=params)
    return status


#Статусы воронок
async def get_all_status_pipeline(ENTITY_ID:str='DEAL_STAGE')->list[dict]:
    """
    ENTITY_ID=DEAL_STAGE - Статусы сделок
    ENTITY_ID=STATUS - Статусы лидов
    """
    items={
            # {'%ENTITY_ID':ENTITY_ID}
            'filter':{'%ENTITY_ID':ENTITY_ID}
            }
    print(items)
    status=await bit.get_all('crm.status.list',params=items)
    # import json
    # with open('status.json', 'w') as file:
    #     json.dump(status, file)
    prepareStatus=[]
    for element in status:
        try:
            if element.get('ENTITY_ID').startswith(ENTITY_ID):
                prepareStatus.append(element)
        except:
            print(f'{element.get('ENTITY_ID')=} {ENTITY_ID=}')
    return prepareStatus

async def get_all_status()->list:
    status=[] 
    status.extend(await get_all_status_pipeline('STATUS'))
    status.extend(await get_all_status_pipeline('DEAL_STAGE'))
    return status




#TODO перенести обновление полей в отдельный модуль

def get_current_datetime():
    """
    Функция для получения текущей даты и времени.
    
    :return: Текущая дата и время в формате 'YYYY-MM-DD HH:MM:SS'
    """
    # current_datetime = datetime.now()+timedelta(hours=3)  # Получаем текущую дату и время
    current_datetime = datetime.now() # Получаем текущую дату и время
    # return current_datetime.strftime('%Y-%m-%dT%H:%M:00+Z')  # Форматируем в строку
    # return '2024-11-07'
    # return '2024-11-07T18:48:54+03:00'
    # return '2024.07.11T00:00:00+03:00'
    # return '2024-11-01T13:51:08+03:00'
    # return '11-11-2024 00:00:00 00:2024-07-11 00Ж00Ж00 00Ж0000'
    # return "'$(date --iso-8601=seconds)'"
    return current_datetime

def prepare_pole_history(stageID:str):
    """Возвращает подходящие название поля обрезаное до 20 знаков"""
    poleHistoryDate=f'UF_CRM_{NAME_APP}'
    # print(f'вход {stageID=}')
    fullPole=poleHistoryDate+stageID
    # print(fullPole)
    # print(len(fullPole))
    idPole=stageID
    if len(fullPole)>20:
        startIndex=len(fullPole)-20

        # fullPole=poleHistoryDate+stageID[startIndex:]
        if startIndex > 0:
            
            fullPole=poleHistoryDate+stageID[:-startIndex] 
            idPole=stageID[:-startIndex]
        else:
            fullPole=poleHistoryDate+stageID
            idPole=stageID[:startIndex]
        # fullPole=fullPole[:20] 
        # idPole=stageID[startIndex:]
    return fullPole, idPole

async def update_history_date_for_deal(dealID, stageID:str=None):
    deal=await get_deal(dealID=dealID)
    # pprint(deal)
    deal=deal
    if stageID is None:
        stageID=deal['STAGE_ID']
        
    
    poleHistory, idStage= prepare_pole_history(stageID=stageID)
    poleHistory=poleHistory.replace(':','_')
    print(f'{poleHistory=}')
    
    historyDealPole=deal[poleHistory]
    print(f'{historyDealPole=} {get_current_datetime()=}')
    # 1/0
    items={
        'id':dealID,
        'fields':{
            poleHistory:get_current_datetime()
        }

    }
    pprint(items)
    if deal[poleHistory]=='':
        await bit.call('crm.deal.update',items=items)

async def get_tags_task(taskID:int):
    items={
        'taskId':taskID,
        'select':['TAGS'],
    }
    
    tags=await bit.call('tasks.task.get',items=items)
    tags=tags['tags']
    return tags


async def get_result_task(taskID:int):
    items={
        'taskId':taskID,
    }
    result=await bit.get_all('tasks.task.result.list',params=items)
    result=result
    return result


async def get_comment_task(taskID:int):
    items={
        'taskId':taskID,
    }
    comment=await bit.get_all('task.commentitem.getlist',params=items)
    comment=comment
    return comment

async def transf_phone(phone:str):
    """79300356988 -> +7 (930) 035-69-88"""
    
    phone=f'+7 ({phone[:3]}) {phone[3:6]}-{phone[6:8]}-{phone[8:]}'
    # phone=phone[1:]
    return phone
async def transf_phone_to_2(phone:str):
    """79308316666 -> +7 (776) 977 67 79"""
    phone=f'+7 ({phone[:3]}) {phone[3:6]} {phone[6:8]} {phone[8:]}'
    return phone
async def transf_phone_to_3(phone:str):
    """79308316666 -> +7 (776) 977 6779"""
    phone=f'+7 ({phone[:3]}) {phone[3:6]} {phone[6:8]}{phone[8:]}'
    return phone


async def find_contact_by_phone(phone:str):
    
    phone=phone[1:]

    items={
        'filter':{
            'PHONE':phone,
        },
        'select':['PHONE','ID','NAME'],
    }
    items2=items.copy()
    items3=items.copy()
    items4=items.copy()
    
    # pprint(items)
    # 1/0
    # contact=await bit.get_all('crm.contact.list',params=items,)
    # contact=await bit.call('crm.contact.list',items=items)
    # pprint(contact)
    contact=None
    startPhones=['+7','8','7','']
    for startPhone in startPhones:
        items['filter']['PHONE']=startPhone+phone
        pprint(items)
        contact=await bit.get_all('crm.contact.list',params=items)
        pprint(contact)
        if contact:
            return contact
        else:
            continue
    
    if contact == []:
        phone1=await transf_phone(phone)
        print(f'{phone1=}')
        phone1=phone1[2:]
        for startPhone in startPhones:
            
            items3['filter']['PHONE']=startPhone+phone1
            pprint(items3)
            contact=await bit.get_all('crm.contact.list',params=items3)
            pprint(contact)
            if contact:
                return contact
            else:
                continue

    if contact ==[]:
        phone2=await transf_phone_to_2(phone)
        print(f'{phone2=}')
        phone2=phone2[2:]
        for startPhone in startPhones:
            items2['filter']['PHONE']=startPhone+phone2
            pprint(items2)
            contact=await bit.get_all('crm.contact.list',params=items2)
            pprint(contact)
            if contact:
                return contact
            else:
                continue
    if contact ==[]:
        phone3=await transf_phone_to_3(phone)
        print(f'{phone3=}')
        phone3=phone3[2:]
        for startPhone in startPhones:
            items4['filter']['PHONE']=startPhone+phone3
            pprint(items4)
            contact=await bit.get_all('crm.contact.list',params=items4)
            pprint(contact)
            if contact:
                return contact
            else:
                continue
    pprint(contact)
    return contact




async def find_deal_by_contact_id(contactID:int):
    items={
        'filter':{
            'CONTACT_ID':contactID,
            'STAGE_SEMANTIC_ID':'P',
            # 'CATEGORY_ID':NEED_CATEGORY,
            '>OPPORTUNITY': 0
        },
        'select':['ID','STAGE_ID','TITLE','*',Deal.file_payment,Deal.room_name,Deal.ostatoc_payment,Deal.telegram_id],
    }
    deal=await bit.get_all('crm.deal.list',params=items)
    return deal


async def update_deal_status(deal_id:int,status:str,filePath:str=None):
    items={
        'ID':deal_id,
        'fields':{
            'STAGE_ID':status,
        }
    }
    if filePath:
        #кодируем файл base64
        import base64
        with open(filePath, 'rb') as file:
            data = file.read()
        data = base64.b64encode(data).decode('utf-8')
        fileName=filePath.split('/')[-1]
        items['fields'][Deal.file_payment]=[{'fileData':[fileName, data]}]
    # pprint(items)
    await bit.call('crm.deal.update',items=items)

async def update_telegram_id(dealID:int,telegram_id:int, chat_room_id:int):
    items={
        'ID':dealID,
        'fields':{
            Deal.telegram_id:telegram_id,
            Deal.chat_room:f'http://{IP_CHAT_ROOM}/chats/{chat_room_id}',
        }
    }
    await bit.call('crm.deal.update',items=items)

async def is_deal_status(dealID:int,status:str):
    deal=await get_deal(dealID=dealID)
    # pprint(deal)
    if deal['STAGE_ID']==status:
        return True
    else:
        return False

async def is_deal_close(dealID:int):
    deal=await get_deal(dealID=dealID)

    if deal['STAGE_SEMANTIC_ID']=='F' or deal['STAGE_SEMANTIC_ID']=='S':
        return True
    else:
        return False


async def send_notification_to_bitrix(telegram_id:int):
    deal=await get_deal_by_telegram_id(telegram_id)

    message=f'новое сообщение от [URL=https://beguest.bitrix24.ru/crm/deal/details/{deal['ID']}/]{deal[Deal.room_name]}[/URL] -> [URL={deal[Deal.chat_room]}]ссылка на чат[/URL]'
    items={
        'USER_ID':deal['ASSIGNED_BY_ID'],
        'MESSAGE':message,
    }
    await bit.call('im.notify.personal.add',items=items)

async def get_deal_by_telegram_id(telegram_id:int):
    items={
        'filter':{
            Deal.telegram_id:telegram_id,
            'STAGE_SEMANTIC_ID':'P'
        },
        'select':['TITLE','ID','ASSIGNED_BY_ID','UF_CRM_1747164098729',Deal.room_name,Deal.chat_room],
        
    }
    # pprint(items)
    result=await bit.get_all('crm.deal.list',params=items)
    # pprint(result)
    return result[0]


async def get_deal_status_and_category(dealID:int)->str:
    """
    Возвращает статус и категорию сделки
    return: tuple(status, category)
    """
    deal=await get_deal(dealID=dealID)
    if isinstance(deal, dict):
        if deal.get("order0000000000"):
            deal = deal["order0000000000"]

    return deal['STAGE_ID'], deal['CATEGORY_ID']

async def main():
    # a=await is_deal_status(dealID=22215,status=Deal.Status.check_payment)
    # pprint(a)
    # +7 932 122-03-01
    contact=await find_contact_by_phone('79321220301')
    pprint(contact)
    # 1/0
    #https://apidocs.bitrix24.ru/api-reference/chats/messages/index.html
    # message='новое сообщение от[URL=https://beguest.bitrix24.ru/crm/deal/details/23115/]Апартаменты на 8 марта 204Д 16[/URL] -> [URL=http://31.129.103.113:8000/chats/1]ссылка на чат[/URL]'
    # contact=await send_notification_to_bitrix(telegram_id=400923372)
    # pprint(contact)
# async def main():
#     # a=await is_deal_status(dealID=22215,status=Deal.Status.check_payment)
#     # pprint(a)
#     # contact=await find_contact_by_phone('79321213415')
#     #https://apidocs.bitrix24.ru/api-reference/chats/messages/index.html
#     message='[URL=http://31.129.103.113:8000/chats/1]ссылка на чат[/URL]'
#     contact=await send_notification_to_bitrix(userID=3719,message=f'Персональное уведомление {message}')
#     pprint(contact)
#     # # 1/0
    # contactID=16317
    contactID=18993
    deal=await find_deal_by_contact_id(contactID)
    pprint(deal)
    # deal=await find_deal_by_contact_id(contactID)
#     # pprint(deal)


if __name__ == '__main__':
    # a=asyncio.run(get_all_event_by_user(userID='138',last_update=datetime.now()-timedelta(days=20)))
    # pprint(a)
    contact=asyncio.run(find_contact_by_phone('77769776779'))
    # pprint(contact)
    # a=asyncio.run(get_contact(28345))
    # a=asyncio.run(get_contact(28205))
    # pprint(a)
    # asyncio.run(test_create_batch())
    # asyncio.run(main())
    # pass
    # asyncio.run(get_userfields(234))