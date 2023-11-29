import requests
from datetime import datetime, timezone
from config.config import load_config
from config.config import logger


class LiveSklad:
    def __init__(self, login, password):
        self.login: str = login
        self.password: str = password
        self.expireDate: datetime = None
        self.token: str = self.get_token()

    def check_expire(self) -> bool:
        if not self.expireDate:
            return True

        current_date = datetime.now(timezone.utc)

        # Удаление миллисекунд из даты и времени
        current_date = current_date.replace(microsecond=0)

        if current_date >= self.expireDate.astimezone(timezone.utc):
            return True
        else:
            return False


    def get_token(self) -> str:
        # Параметры запроса
        url = "https://api.livesklad.com/auth"
        data = {
            "login": self.login,
            "password": self.password
        }

        # Отправка POST-запроса на авторизацию
        response = requests.post(url, data=data)

        # Проверка статуса ответа
        if response.status_code == 200:
            # Авторизация прошла успешно
            logger.info('Успешная авторизация! Токен доступа:', response.json())

            # Преобразование строки в объект datetime
            res = response.json()["expireDate"].replace('Z', '+00:00')
            self.expireDate = datetime.fromisoformat(res).replace(microsecond=0)

            return response.json()["token"]
        else:
            # Произошла ошибка при авторизации
            logger.info('Ошибка авторизации. Код ошибки:', response.status_code)

    def get_zakaz(self, num) -> str:
        if self.check_expire():  #если токен закончился, выпустить новый
            self.token = self.get_token()

        # Параметры запроса
        url = 'https://api.livesklad.com/company/orders'
        if num[0].lower() == "a" or \
                num[0].lower() == "а":
            try:
                num = int(num[1:])
            except Exception as e:
                return f"Неверная строка заказа. Ошибка: {e}"
        params = {
            'num': num
        }

        # Заголовки запроса с токеном доступа
        headers = {
            'Authorization': self.token
        }

        # Отправка GET-запроса
        response = requests.get(url, params=params, headers=headers)

        # Проверка статуса ответа
        if response.status_code == 200:
            # Запрос выполнен успешно
            res = response.json()
            return f"{res['data'][0]['typeDevice']} {res['data'][0]['device']}." \
                   f" Статус заказа: {res['data'][0]['status']['name']}"
        else:
            # Произошла ошибка при выполнении запроса
            return f"Ошибка запроса. Код ошибки: {response.status_code}"


config = load_config()
livesklad: LiveSklad = LiveSklad(config.ls.login,
                                 config.ls.password)