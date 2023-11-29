from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

router: Router = Router()


# хендлеры для остальных ответов
@router.message(StateFilter(default_state))
async def send_echo_1(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')


@router.message(~StateFilter(default_state))
async def send_echo_2(message: Message):
    await message.reply(text='Введены неверные данные, попробуйте еще раз')