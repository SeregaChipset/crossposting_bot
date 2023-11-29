import requests
import aiohttp
import pathlib, sys
from config.config import logger, load_cfg
from aiogram import Bot
from aiogram.types import Message, PhotoSize, InputMediaPhoto
import difflib, json


async def get_media(bot, album: list[Message] = None, photo: PhotoSize = None, caption: str = None) -> list[InputMediaPhoto]:
    media_group = []
    if album:
        for msg in album:
            if msg.photo:
                file_id = msg.photo[-1].file_id
                photo_file = await bot.get_file(file_id)
                print(photo_file.file_path)
                media_group.append(InputMediaPhoto(media=file_id))
            else:
                print(msg)
        media_group[0].parse_mode = 'HTML'
        media_group[0].caption = caption
    else:
        media_group = [InputMediaPhoto(media=photo.file_id, caption = caption, parse_mode = 'HTML')]
    return media_group

def get_text_post(my_dict: dict, vk: bool=False, vk_post_id: str = None, product_href: str = None) -> str:
    if not vk:
        my_dict["name"] = f'<b>{my_dict["name"]}</b>'
    text = f'{my_dict["name"]}\n\n' \
           f'{my_dict["description"]}\n\n' \
           f'Цена: {my_dict["price"]} ₽\n\n' \
           f'{load_cfg()["podval"]}'
    if not vk: text += f'\n\n <a href="{vk_post_id}">Ссылка на VK</a>'
    if vk and product_href: text += f'\n\n {product_href}'
    return text


async def save_img_tg(bot: Bot, item: Message) -> str:
    photo_id = item.media
    photo_file = await bot.get_file(photo_id)
    photo_url = f'https://api.telegram.org/file/bot{bot.token}/{photo_file.file_path}'
    response = requests.get(photo_url)
    if response.status_code == 200:
        with open(f'{pathlib.Path(sys.argv[0]).parent}/tmp/{photo_id}.jpg', 'wb') as f:
            f.write(response.content)
            logger.info('Фотография сохранена.')
            return f'{photo_id}.jpg'
    else:
        logger.info('Ошибка при загрузке фотографии.')


async def get_upload_server(token_vk: str, album_id: str) -> str:
    upload_url = 'https://api.vk.com/method/photos.getUploadServer'
    params ={
        'access_token': token_vk,
        'album_id': album_id,
        'v': '5.154'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(upload_url, params=params) as response:
            if response.status == 200:
                upload_server = (await response.json())['response']['upload_url']
            else:
                logger.info('Не удалось получить upload_server.')
                upload_server = None
    return upload_server


async def upload_image_vk(token_vk: str, photo_name: str, upload_server: str, album_id: str) -> int:
    with open(f'{pathlib.Path(sys.argv[0]).parent}/tmp/{photo_name}', 'rb') as photo_file:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file',
                           photo_file,
                           filename=photo_name,
                           content_type='image/jpeg')
            async with session.post(upload_server, data=data) as response:
                if response.status == 200:
                    upload_response = await response.text()
                    upload_response_json = json.loads(upload_response)
                else:
                    logger.info('Не удалось загрузить фотографию.')
    save_url = 'https://api.vk.com/method/photos.save'
    params = {
        'access_token': token_vk,
        'album_id': album_id,
        'server': upload_response_json['server'],
        'photos_list': upload_response_json['photos_list'],
        'hash': upload_response_json['hash'],
        'v': '5.154'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(save_url, params=params) as save_response:
            if response.status == 200:
                save_response_json = await save_response.json()
                photo_id = save_response_json['response'][0]['id']
                owner_id = save_response_json['response'][0]['owner_id']
                logger.info(f"Фотография успешно загружена.\nOwner ID: {owner_id}\nPhoto ID: {photo_id}")
                return f'photo{owner_id}_{photo_id}'
            else:
                logger.info('Не удалось сохранить фотографию.')


async def post_wall_vk(token_vk: str, group_vk: str, text: str, img_list: list) -> int:
    url = (f"https://api.vk.com/method/wall.post?access_token={token_vk}&owner_id=-{group_vk}&"
           f"attachments={','.join(img_list)}&from_group=1&message={text}&v=5.154")
    params = {
        'access_token': token_vk,
        'owner_id': f'-{group_vk}',
        'attachments': ','.join(img_list),
        'from_group': 1,
        'message': text,
        'v': '5.154'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                logger.info("Пост размещен.")
                post_id = await response.json()
                post_id = post_id['response']['post_id']
            else:
                logger.info("Не удалось разместить пост.")
                post_id = None
    return post_id


async def post_market(token_vk: str, group_vk: str, my_dict: dict, photo_name: str, v: str = '5.154'):
    # функция для постинга товаров

    # вспомогательная функция формирования словаря id и имен категорий
    def get_cat(cat_list: list, ret_dict: dict = None) -> dict:
        if not ret_dict:
            ret_dict = {}
        for cat in cat_list:
            if 'children' in cat:
                ret_dict.update(get_cat(cat['children'], ret_dict))
            else:
                if 'id' in cat and 'name' in cat:
                    ret_dict.update({cat['name'].strip(): cat['id']})
        return ret_dict

    def get_match_words(text: str, categories: dict) -> list:
        # поиск схожей категории
        text_list = text.lower().split()
        selected_words = []
        for sentence_word in text_list:
            close_matches = difflib.get_close_matches(sentence_word, categories.keys(), n=1, cutoff=0.3)
            if close_matches:
                selected_words.append(close_matches[0])
        logger.info(f"Выбранные слова из списка: {selected_words}")
        if not selected_words:
            raise Exception('Список выбранных слов пуст')
        return selected_words

    async def check_response(response):
        if response.status == 200:
            logger.info('Запрос товарки успешно выполнен')
            result = await response.json()
            if 'error' in result:
                raise Exception(f'Возникла ошибка: {result["error"]}')
            return result
        else:
            raise Exception(f'Ошибка, статус: {response.status}')

    # получение списка категорий
    async with aiohttp.ClientSession() as session:

        url = 'https://api.vk.com/method/market.getCategories'
        params = {
            'access_token': token_vk,
            'v': v,
        }
        async with session.get(url, params=params, ssl=False) as response:
            market_response = await check_response(response)
            categories = get_cat(market_response['response']['items'][1]['children'])

        # поиск схожей категории
        try:
            selected_words = get_match_words(my_dict["name"], categories)
        except Exception as e:
            logger.error(f'Нет схожих слов для категории: {e}')
            categories = {'error': '1'}
            selected_words = ['error']

    # Получение сервера для загрузки фото
        url = 'https://api.vk.com/method/photos.getMarketUploadServer'
        params = {
            'access_token': token_vk,
            'group_id': group_vk,
            'v': v
        }
        async with session.get(url, params=params, ssl=False) as response:
            upload_url = await check_response(response)
            upload_url = upload_url['response']['upload_url']

        # Загрузка фото на сервер
        file_path = f'{pathlib.Path(sys.argv[0]).parent}/tmp/{photo_name}'
        with open(file_path, 'rb') as file:
            data = aiohttp.FormData()
            data.add_field('file',
                           file,
                           filename=photo_name,
                           content_type='image/jpeg')
            async with session.post(upload_url, data=data, ssl=False) as response:
                if response.status == 200:
                    photo = await response.text()
                    photo = json.loads(photo)
                else:
                    raise Exception(response.status)

        # Сохранение фото на сервере VK
        url = 'https://api.vk.com/method/photos.saveMarketPhoto'
        params = {
            'access_token': token_vk,
            'group_id': group_vk,
            'photo': photo['photo'],
            'server': photo['server'],
            'hash': photo['hash'],
            'v': v
        }
        async with session.get(url, params=params, ssl=False) as response:
            saved_photo = await check_response(response)

        # Добавление товара
        url = 'https://api.vk.com/method/market.add'
        params = {
            'access_token': token_vk,
            'owner_id': f"-{group_vk}",
            'name': my_dict["name"],
            'description': my_dict["description"],   #description should be at least 10 letters length
            'category_id': categories[selected_words[0]],
            'price': my_dict["price"],
            'main_photo_id': saved_photo['response'][0]['id'],
            'v': v
        }
        async with session.get(url, params=params, ssl=False) as response:
            product = await check_response(response)
        logger.info(f'товар успешно добавлен {product["response"]["market_item_id"]}, категория: {categories[selected_words[0]]}')

        # Получаем список подборок
        url = 'https://api.vk.com/method/market.getAlbums'
        params = {
            'access_token': token_vk,
            'owner_id': f'-{group_vk}',
            'count': 100,
            'v': v
        }
        async with session.get(url, params=params, ssl=False) as response:
            albums = await check_response(response)
            albums = {item['title'] : item['id'] for item in albums['response']['items']}

        try:
            selected_words = get_match_words(my_dict["name"], albums)
        except Exception as e:
            logger.error(f'Нет схожих слов для подборки: {e}')
            selected_words = []

        # Добавляем товар в подборку
        if selected_words:
            url = 'https://api.vk.com/method/market.addToAlbum'
            params = {
                'access_token': token_vk,
                'owner_id': f'-{group_vk}',
                'item_ids': product['response']['market_item_id'],
                'album_ids': albums[selected_words[0]],
                'v': v
            }
            async with session.get(url, params=params, ssl=False) as response:
                fin = await check_response(response)
            logger.info(f'товар добавлен в подборку {fin["response"]}')

        return product["response"]["market_item_id"]
