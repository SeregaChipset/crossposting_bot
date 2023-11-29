import sys, pathlib
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from config.config import load_cfg, save_cfg
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from fsm import FSMSettings
from keyboards.main_kbd import markup_cancel
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, InputMediaPhoto)


router: Router = Router()

TEST = (f'<b>Видеокарта ASUS GeForce RTX 2060 Dual EVO OC Edition </b>\n\n'
        f'обеспечит высокую производительность вашего ПК в самых разных задачах - будь то игры на высоких настройках, монтаж видео или ретушь фото. В основе данной модели используется чип, выполненный с применением микроархитектуры Turing. Он работает в частотном диапазоне от 1365МГц до 1785МГц, что вкупе с 6 ГБ встроенной памяти позволяет обрабатывать даже самые сложные задачи.'
        f'Видеокарта ASUS GeForce RTX 2060 отличается лаконичным дизайном и встроенной подсветкой некоторых элементов. Подключение производится при помощи интерфейса PCI-E, для дополнительного питания используется разъем 8-pin. Для периферии предусмотрено 2 выхода HDMI, DVI-D, а также DisplayPort.\n\n'
        f'Цена: 15990 ₽\n\n')


# хендлеры настроек
@router.callback_query(StateFilter(default_state), F.data == '/setting')
async def process_setting(callback: CallbackQuery, state: FSMContext):
    post_view_button = InlineKeyboardButton(
        text='Пример поста 📝',
        callback_data='/post_view'
    )
    podval_button = InlineKeyboardButton(
        text='Подвал 👹️',
        callback_data='/podval'
    )
    tokens_button = InlineKeyboardButton(
        text='Токены 🤖',
        callback_data='/tokens'
    )
    cancel_button = InlineKeyboardButton(
        text='Назад в меню ❌',
        callback_data='/cancel'
    )
    keyboard: list[list[InlineKeyboardButton]] = [
        [post_view_button, podval_button], [tokens_button, cancel_button]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(
        text='<b>Настройки</b>\n\n',
        reply_markup=markup
    )
    await state.set_state(FSMSettings.fill_settings)


@router.callback_query(StateFilter(FSMSettings.fill_settings), F.data == '/post_view')
async def post_view(callback: CallbackQuery):
    path = pathlib.Path(sys.argv[0]).parent
    media_group = [InputMediaPhoto(media=types.FSInputFile(f'{path}/sample_photo/photo_1.jpg'),
                                   caption=f'{TEST}{load_cfg()["podval"]}', parse_mode = 'HTML'),
                   InputMediaPhoto(media=types.FSInputFile(f'{path}/sample_photo/photo_2.jpg')),
                   InputMediaPhoto(media=types.FSInputFile(f'{path}/sample_photo/photo_3.jpg'))]
    await callback.message.answer_media_group(
        media=media_group
    )
    await callback.message.answer(
        text='Примерный вид поста в телеге (в вк будет выглядеть иначе)',
        reply_markup=markup_cancel
    )


@router.callback_query(StateFilter(FSMSettings.fill_settings), F.data == '/podval')
async def podval_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text='<b>Введите новый текст, который будет добавлен в нижнюю часть объявлений. Для отмены, вернитесь в меню</b>\n\n'
             f'Старый текст подвал:\n{load_cfg()["podval"]}',
        parse_mode='HTML',
        reply_markup=markup_cancel
    )
    await state.set_state(FSMSettings.fill_podval)


@router.message(StateFilter(FSMSettings.fill_podval), F.text)
async def process_podval_sent(message: Message):
    cfg = load_cfg()
    cfg["podval"] = message.text
    save_cfg(cfg)
    await message.answer(text='Отлично!\n\nТеперь этот текст будет во всех сообщениях',
                         reply_markup=markup_cancel)


@router.message(StateFilter(FSMSettings.fill_podval))
async def warning_not_podval(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Введите текст подвала еще разок\n\n',
        reply_markup=markup_cancel
    )


@router.callback_query(StateFilter(FSMSettings.fill_settings), F.data == '/tokens')
async def token_edit(callback: CallbackQuery, state: FSMContext):
    cfg = load_cfg()
    await callback.message.answer(
        #text='<b>Введите новый токен вк</b>\n\n',
        text = 'Редактирование токенов заблокировано\n\n'
               f'Токен вк: {cfg["token_vk"]}\n\n'
               f'id альбома для картинок: {cfg["album_id"]}\n\n'
               f'id группы для вк постинга: {cfg["group_vk"]}\n\n'
               f'канал для тг постинга: {cfg["group_tg"]}\n\n',
        parse_mode='HTML',
        reply_markup=markup_cancel
    )
    #await state.set_state(FSMSettings.fill_token)


@router.message(StateFilter(FSMSettings.fill_token), F.text)
async def process_tokenvk_sent(message: Message, state: FSMContext):
    cfg = load_cfg()
    cfg["token_vk"] = message.text
    save_cfg(cfg)
    await message.answer(text='Принято!\n\n'
                             f'<b>Введите новый id группы</b>\n\n',
                         parse_mode='HTML',
                         reply_markup=markup_cancel)
    await state.set_state(FSMSettings.fill_group)


@router.message(StateFilter(FSMSettings.fill_token))
async def warning_not_token(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Введите токен еще разок\n\n',
        reply_markup=markup_cancel
    )

@router.message(StateFilter(FSMSettings.fill_group), F.text)
async def process_group_sent(message: Message, state: FSMContext):
    cfg = load_cfg()
    cfg["group_tg"] = message.text
    save_cfg(cfg)
    await message.answer(text='Данные сохранены!\n\n',
                         reply_markup=markup_cancel)
    await state.set_state(FSMSettings.fill_group)


@router.message(StateFilter(FSMSettings.fill_group))
async def warning_not_group(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Введите ид группы еще разок\n\n',
        reply_markup=markup_cancel
    )
