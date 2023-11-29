from aiogram import Router, F
from aiogram.filters import StateFilter
from service.livesklad import livesklad
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from fsm import FSMZakaz
from keyboards.main_kbd import markup_cancel
from aiogram.types import CallbackQuery, Message


router: Router = Router()


# хендлеры заказа
def is_zakaz(message: Message) -> bool:  #фильтр проверки на номер заказа
    if message.text[0].lower() == "a" or \
        message.text[0].lower() == "а":
        return message.text[1:].isdigit()
    else:
        return message.text.isdigit()


@router.callback_query(StateFilter(default_state), F.data == '/zakaz')
async def process_zakaz(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text='Введите номер заказа', reply_markup=markup_cancel)
    # Устанавливаем состояние ожидания ввода заказа
    await state.set_state(FSMZakaz.fill_zakaz)

@router.message(StateFilter(FSMZakaz.fill_zakaz), is_zakaz)
async def view_zakaz(message: Message):
    await message.answer(text=livesklad.get_zakaz(message.text), reply_markup=markup_cancel)

@router.message(StateFilter(FSMZakaz.fill_zakaz))
async def warning_not_zakaz(message: Message):
    await message.answer(
        text='Не похоже на номер заказа\n\n'
             'Пробуем еще раз\n\n',
        reply_markup=markup_cancel
    )
