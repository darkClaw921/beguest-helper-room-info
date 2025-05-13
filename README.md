# Помогает с информацией по квартире

## Работа с Яндекс.Диском

Для работы с модулем `yadisk_downloader.py` необходимо получить следующие переменные:
- `TOKEN_YD` - OAuth токен для доступа к API Яндекс.Диска
- `APLICATION_ID` - идентификатор приложения
- `APLICATION_SECRET` - секрет приложения

### Как получить переменные для Яндекс.Диска

1. **Регистрация приложения в Яндексе:**
   - Перейдите на страницу [Яндекс OAuth](https://oauth.yandex.ru/)
   - Нажмите на кнопку "Зарегистрировать новое приложение"
   - Заполните форму:
     - Название приложения: укажите название вашего проекта
     - Платформа: выберите подходящую платформу (веб-сервис или др.)
     - Данные для доступа: выберите "Яндекс.Диск REST API"
     - Укажите Callback URI: если это веб-сервис (или используйте `https://example.com` для тестирования)

2. **Получение APLICATION_ID и APLICATION_SECRET:**
   - После регистрации приложения вам будут предоставлены:
     - ID приложения (ClientID) - это значение `APLICATION_ID`
     - Пароль приложения (Client secret) - это значение `APLICATION_SECRET`

3. **Получение OAuth токена:**
   - Сформируйте URL для авторизации:
   ```
   https://oauth.yandex.ru/authorize?response_type=token&client_id=APLICATION_ID
   ```
   - Перейдите по этому URL в браузере
   - Авторизуйтесь в своем аккаунте Яндекса
   - Разрешите доступ приложению к Яндекс.Диску
   - После успешной авторизации вы будете перенаправлены на указанный Callback URI с токеном в параметрах URL
   - Значение параметра `access_token` в URL - это `TOKEN_YD`

4. **Сохранение переменных:**
   - Создайте файл `.env` в корне проекта
   - Добавьте полученные переменные:
   ```
   TOKEN_YD=<ваш_токен>
   APLICATION_ID=<ваш_ID_приложения>
   APLICATION_SECRET=<ваш_секрет_приложения>
   ```

### Пример использования

```python
from yadisk_downloader import YandexDiskDownloader

# Создание экземпляра класса
downloader = YandexDiskDownloader()

# Скачивание файла
file_path = "/ИНФО ПО КВАРТИРАМ/Азина 22 корп.2 -198 (11 этаж)/Как выглядит квартира.mov"
save_path = "./downloads/квартира.mov"
result = downloader.download_file(file_path, save_path)

# Асинхронное скачивание
import asyncio
async def download_async():
    result = await downloader.download_file_async(file_path, save_path)
    return result

asyncio.run(download_async())
```