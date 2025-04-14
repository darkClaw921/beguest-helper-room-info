import urllib
import urllib.parse
# 
# Исходная ссылка
def encode_yandex_url(original_url):
    # Декодируем URL, если он уже содержит кодированные части
    decoded_url = original_url.replace('%20', ' ').replace('%2F', '/').replace('%3A', ':').replace('%2C', ',').replace('%3D', '=').replace('%2B', '+')
    # print(f"Декодированный URL: {decoded_url}")

    # Разделяем URL на части
    url_parts = decoded_url.split('?')
    base_url = url_parts[0]
    if len(url_parts) > 1:
        params_str = url_parts[1]
        params = params_str.split('&')
        
        encoded_params = []
        for param in params:
            if param.startswith('url='):
                # Обрабатываем специальный параметр url отдельно
                param_parts = param.split('=', 1)
                param_value = param_parts[1]
                
                # Разделяем значение параметра url на части
                url_value_parts = param_value.split('/')
                
                # Кодируем только путь после домена
                encoded_url_parts = []
                for i, part in enumerate(url_value_parts):
                    if ":" in part and i < 3:  # Для протокола и домена
                        encoded_url_parts.append(part)
                    else:
                        encoded_url_parts.append(urllib.parse.quote(part, safe=''))
                
                encoded_param_value = '/'.join(encoded_url_parts)
                encoded_params.append(f"url={encoded_param_value}")
            else:
                # Для других параметров просто кодируем значение
                param_parts = param.split('=', 1)
                if len(param_parts) > 1:
                    param_name = param_parts[0]
                    param_value = param_parts[1]
                    encoded_param_value = urllib.parse.quote(param_value, safe='')
                    encoded_params.append(f"{param_name}={encoded_param_value}")
                else:
                    encoded_params.append(param)
        
        # Собираем URL обратно
        encoded_url = f"{base_url}?{'&'.join(encoded_params)}"
    else:
        # Если нет параметров, просто кодируем части пути
        url_parts = decoded_url.split('/')
        encoded_parts = []
        for i, part in enumerate(url_parts):
            if i < 3:  # Для протокола и домена
                encoded_parts.append(part)
            else:
                encoded_parts.append(urllib.parse.quote(part, safe=''))
        
        encoded_url = '/'.join(encoded_parts)

    # print(f"Закодированный URL: {encoded_url}")
    return encoded_url
if __name__ == '__main__':
    pass