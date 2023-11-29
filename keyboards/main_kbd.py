from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

cancel_button = InlineKeyboardButton(
    text='Назад в меню ❌',
    callback_data='/cancel'
)
kbd_cancel: list[list[InlineKeyboardButton]] = [
    [cancel_button, ]
]
markup_cancel = InlineKeyboardMarkup(inline_keyboard=kbd_cancel)