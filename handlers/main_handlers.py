from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message


router: Router = Router()


class AdminFilter(BaseFilter):  # [1]
    async def __call__(self, message: Message) -> bool:  # [3]
        return message.from_user.username in {'SeregaChipset', 'Veronica_Friesen', 'roxxenya', 'ChipsetPlus'}

@router.channel_post(Command(commands='get_chat_id'))
async def get_chat_id(message: Message):
    chat_id = message.chat.id
    await message.reply(f"Chat ID: {chat_id}")


@router.message(CommandStart(), StateFilter(default_state), AdminFilter())
async def process_start_command(message: Message):
    post_button = InlineKeyboardButton(
        text='Пост 📝',
        callback_data='/post'
    )
    zakaz_button = InlineKeyboardButton(
        text='Заказ 🛠️',
        callback_data='/zakaz'
    )
    setting_button = InlineKeyboardButton(
        text='Настройки ⚙️',
        callback_data='/setting'
    )
    keyboard: list[list[InlineKeyboardButton]] = [
        [post_button, zakaz_button, setting_button]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        text='<b>Кросспостинг бот разместит сообщение в телеге и вк</b>\n\n'
             '1) Последовательное создание поста; \n'
             '2) Посмотреть информацию по заказу livesklad; \n'
             '3) Настройки(токены, подвал, пример поста). \n',
        reply_markup=markup
    )


# хендлеры отмены
@router.callback_query(StateFilter(default_state), F.data == '/cancel')
async def process_cancel_command(message: Message):
    await message.answer(
        text='Отменять нечего.'
    )


@router.callback_query(~StateFilter(default_state), F.data == '/cancel')
async def process_cancel_command_state(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        text='Начальное меню.\nВсе данные удалены.'
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()
    await process_start_command(callback.message)


