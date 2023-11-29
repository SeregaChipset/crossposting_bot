from dataclasses import dataclass
import logging
import pickle
from environs import Env

env: Env = Env()
env.read_env()

# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}

# Инициализируем логгер
logger = logging.getLogger(__name__)
# Конфигурируем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')
# Выводим в консоль информацию о начале запуска бота
logger.info('Starting bot')

@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту

@dataclass
class LS:
    login: str            # логин и пароль для доступа к livesklad
    password: str


@dataclass
class Config:
    tg_bot: TgBot
    ls: LS
    token_vk: str
    group_vk: str
    group_id: str
    album_id: str


def load_config() -> Config:
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN')),
                  ls=LS(login=env('LOGIN_LS'), password=env('PASSWORD_LS')),
                  token_vk=env('TOKEN_VK'), group_vk=env('GROUP_VK'),
                  group_id=env('GROUP_TG'), album_id=env('ALBUM_ID'))


def load_cfg() -> dict:
    try:
        with open('cfg.pkl', 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        cfg = {
            # sample vk
            'token_vk': env('TOKEN_VK'),
            'group_vk': env('GROUP_VK'),
            'group_tg': env('GROUP_TG'),
            'album_id': env('ALBUM_ID'),
            'podval': ''
        }
        return cfg


def save_cfg(cfg: dict):
    with open('cfg.pkl', 'wb') as file:
        pickle.dump(cfg, file)