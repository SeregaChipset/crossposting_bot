from aiogram import Router, F, Bot
from aiogram.filters import StateFilter, BaseFilter
from config.config import load_cfg
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from fsm import FSMPost
import service.post_service as post_service
from keyboards.main_kbd import markup_cancel
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize, InputMediaPhoto, ContentType as CT)


router: Router = Router()

class PhotoFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict:
        if message.photo:
            if message.photo[-1].width >= 400 and message.photo[-1].height >= 400:
                if message.media_group_id:
                    return True
                else:
                    return {'photo': message.photo[-1]}
        return False


# хендлеры поста
@router.callback_query(StateFilter(default_state), F.data == '/post')
async def process_post_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text='Введите название', reply_markup=markup_cancel)
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMPost.fill_name)


@router.message(StateFilter(FSMPost.fill_name), F.text)
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text='Хорошо!\n\nА теперь введите описание'
                             '\n\n(не менее 10 символов)',
                         reply_markup=markup_cancel)
    await state.set_state(FSMPost.fill_description)


@router.message(StateFilter(FSMPost.fill_name))
async def warning_not_name(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Пробуем еще раз ввести название\n\n',
        reply_markup=markup_cancel
    )


@router.message(StateFilter(FSMPost.fill_description), F.text & (F.text.len() > 10))
async def process_description_sent(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(text='Отлично!\n\nТеперь цену(только цифры, без копеек)',
                         reply_markup=markup_cancel)
    await state.set_state(FSMPost.fill_price)


@router.message(StateFilter(FSMPost.fill_description))
async def warning_not_description(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Пробуем еще раз ввести описание, от 10 символов\n\n',
        reply_markup=markup_cancel
    )


@router.message(StateFilter(FSMPost.fill_price), F.text.isdigit())
async def process_price_sent(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer(text='Отлично!\n\nПоследний шаг - отправьте фото)'
                             '\n\n(Можно несколько. С разрешением от 400х400)',
                         reply_markup=markup_cancel)
    await state.set_state(FSMPost.fill_photo)


@router.message(StateFilter(FSMPost.fill_price))
async def warning_not_price(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Введите цену(только цифры, без копеек)\n\n',
        reply_markup=markup_cancel
    )


@router.message(StateFilter(FSMPost.fill_photo), PhotoFilter())
async def process_photo_sent(message: Message, bot: Bot, state: FSMContext,
                             album: list[Message] = None, photo: PhotoSize = None):
    print(message.model_dump_json())
    print(f'album: {album}\nphoto: {photo}')
    yes_button = InlineKeyboardButton(
        text='Да ✅',
        callback_data='yes'
    )
    tovar_button = InlineKeyboardButton(
        text='Да +товар 🛒',
        callback_data='tovar'
    )
    no_button = InlineKeyboardButton(
        text='Нет ❌',
        callback_data='/cancel'
    )
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_button, tovar_button, no_button]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    my_dict = await state.get_data()
    caption = post_service.get_text_post(my_dict)

    media_group = await post_service.get_media(bot, album, photo, caption)

    await state.update_data(album=album)
    await state.update_data(photo=photo)
    await state.update_data(photo_group=media_group)

    await message.answer_media_group(
        media=media_group,
    )
    await message.answer(text='Размещать?',
                         reply_markup=markup)

    await state.set_state(FSMPost.approve)


@router.message(StateFilter(FSMPost.fill_photo))
async def warning_not_photo(message: Message):
    await message.answer(
        text='Что то пошло не так\n\n'
             'Отправьте фото(400х400 и больше)\n\n',
        reply_markup=markup_cancel
    )


@router.callback_query(StateFilter(FSMPost.approve), F.data.in_(['yes', 'tovar']))
async def warning_approve(callback: CallbackQuery, state, bot: Bot):
    my_dict = await state.get_data()
    cfg = load_cfg()

    photo_names = []
    for item in my_dict['photo_group']:
        photo_names.append(await post_service.save_img_tg(bot, item))

    if callback.data == 'tovar':
        product_id =await post_service.post_market(cfg['token_vk'], cfg['group_vk'],
                                       my_dict, photo_names[0])
        product_link = f'https://vk.com/market-{cfg["group_vk"]}?w=product-{cfg["group_vk"]}_{product_id}'
        text = post_service.get_text_post(my_dict, vk=True, product_href=product_link)
    else:
        text = post_service.get_text_post(my_dict, vk=True)

    postec = []
    upload_server = await post_service.get_upload_server(cfg['token_vk'], cfg['album_id'])
    for photo_name in photo_names:
        postec.append(await post_service.upload_image_vk(cfg['token_vk'], photo_name, upload_server,
                                                          cfg['album_id']))

    post_id = await post_service.post_wall_vk(cfg["token_vk"], cfg["group_vk"], text, postec)

    caption = post_service.get_text_post(my_dict, vk=False, vk_post_id=f'https://vk.com/public{cfg["group_vk"]}?w=wall-{cfg["group_vk"]}_{post_id}')
    media = await post_service.get_media(bot, my_dict['album'], my_dict['photo'], caption)
    tg_res = await bot.send_media_group(chat_id=cfg['group_tg'], media=media)
    tg_post = f'https://t.me/{tg_res[0].chat.username}/{tg_res[0].message_id}'

    await callback.message.answer(
        text='<b>Посты размещены!</b>\n\n'
             f'<a href="{tg_post}">TG Ссылка на пост</a>\n\n'
             f'<a href="https://vk.com/public{cfg["group_vk"]}?w=wall-{cfg["group_vk"]}_{post_id}">VK Ссылка на пост</a>\n\n',
        parse_mode="HTML",
        reply_markup=markup_cancel,
        disable_web_page_preview=True
    )
