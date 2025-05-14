


from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel

# Создаем экземпляр FastAPI
app = FastAPI(title="API с параметром ID", 
              description="Простое API, которое принимает параметр id",
              version="1.0.0")

# Определяем модель ответа
class Response(BaseModel):
    message: str
    id: int

@app.get("/items/{item_id}", response_model=Response)
async def read_item(item_id: int):
    """
    Получить элемент по ID
    
    - **item_id**: ID элемента для получения
    """
    # Здесь можно добавить логику обработки ID
    # Например, поиск в базе данных
    
    # Проверка на допустимость ID
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="ID должен быть положительным числом")
    
    return Response(message=f"Получен элемент с ID", id=item_id)

@app.get("/", response_model=dict)
async def root():
    """
    Корневой маршрут, возвращает информацию о API
    """
    return {"message": "Добро пожаловать в API! Используйте /items/{item_id} для получения элемента по ID"}

