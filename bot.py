import asyncio
import datetime
import re
import aiohttp
import requests
from urllib.parse import urlencode

from aiogram.dispatcher import FSMContext, filters
from aiogram.utils import executor

from bs4 import BeautifulSoup

import aiogram
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.bot import api
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, \
    message_id, message, Chat, ContentType
from anticaptchaofficial.hcaptchaproxyless import *
from sqlite import UserDB, CourseDB, RequestDB

import config
# import utils
# from utils import check_balance

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
API_KEY = ""

#  инициализируем базу данных
user_db = UserDB('swdatabase.db')
course_db = CourseDB('swdatabase.db')
request_db = RequestDB('swdatabase.db')

# =====================================================================================================
# ====================================== ПРИВЕТСВИЕ ===================================================
# =====================================================================================================
session = requests.Session()
admins = [839490080]
courses_per_day = {}


# =====================================================================================================
# ====================================== ПРОВЕРКА БАЛАНСА =============================================
# =====================================================================================================
async def get_balance(API_KEY):
    url = 'https://api.anti-captcha.com/getBalance'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {'clientKey': API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                data = await response.json()
                return data['balance']
            else:
                return None


async def send_notification(bot: Bot, balance):
    text = f"<b>⚠️ Внимание! Чуваки, пора платить решалам!</b>\n<b>➖ Баланс:</b> <code>{balance}</code>$!"
    await bot.send_message(chat_id='-834856996', text=text)


async def check_balance(bot: Bot):
    while True:
        balance = await get_balance(API_KEY)
        print(balance)
        if balance is not None and balance <= 1:
            await send_notification(bot, balance)
            break
        await asyncio.sleep(30)


async def on_startup(dp):
    await bot.send_message(chat_id='-834856996', text='<b>🚀 Bot started!</b>')
    asyncio.create_task(check_balance(bot))


# =====================================================================================================
# ====================================== РАССЫЛКА =====================================================
# =====================================================================================================
@dp.message_handler(content_types=ContentType.PHOTO)
async def save_media_id(message: types.Message, state: FSMContext):
    # сохраняем идентификатор медиаконтента в состоянии бота
    await state.set_data({'media_id': message.photo[-1].file_id})
    await message.answer('Идентификатор медиаконтента сохранен.')


@dp.message_handler(commands=['alerts'])
async def send_alerts(message: types.Message):
    if message.from_user.id not in admins:
        return

    users = user_db.get_all_users()

    text = message.text.replace('/alerts ', '')

    # получаем сохраненный идентификатор медиаконтента из состояния бота
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()
    media_id = data.get('media_id', None)

    # создаем список медиа
    media = []
    if media_id:
        media.append(types.InputMediaPhoto(media=media_id, caption=text))
    else:
        media.append(types.InputMediaDocument(media=text))

    for user in users:
        try:
            # отправляем медиа-контент и текст сообщения в одном сообщении
            await bot.send_media_group(user.id, media=media)
            # await bot.send_message(user.id, text)
        except aiogram.utils.exceptions.BotBlocked:
            print(f"User {user.id} has blocked the bot")
            continue
        except aiogram.utils.exceptions.ChatNotFound:
            print(f"User {user.id} not found")
            continue
        except Exception as e:
            print(f"Error while sending message to user {user.id}: {e}")
            continue

    await message.answer("Рассылка завершена.")


# =====================================================================================================
# ====================================== СТАРТ, ОБРАБОТКА МЕНЮ ========================================
# =====================================================================================================
@dp.message_handler(commands=['start'])
async def start_handler(message: aiogram.types.Message):
    user_db.create()
    course_db.create()
    request_db.create()
    request_db.add_request(message.from_user.id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if not user_db.user_exist(message.from_user.id):
        user_db.add_user(message.from_user.id)
        username = message.from_user.username
        name = f"@{username}" if username else f"{message.from_user.first_name} {message.from_user.last_name}"
        await bot.send_message('-834856996', f"➖ {name} - новый пользователь")

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton('🤖 Услуги кодера'),
        KeyboardButton('⚙️ Статистика')
    )
    await message.answer('👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/', reply_markup=keyboard)

# @dp.callback_query_handler(lambda query: query.data == 'check_subscription')
# async def check_subscription_handler(query: types.CallbackQuery):
#     user_id = query.from_user.id
#     chat_id = '-1001735705501'
#     member = await bot.get_chat_member(chat_id, user_id)
#     if member.status == 'left':
#         keyboard = InlineKeyboardMarkup()
#         keyboard.add(InlineKeyboardButton(text='Подписаться на канал', url='https://t.me/rare_hood'))
#         await bot.send_message(chat_id=query.message.chat.id, text='Вы не подписаны на канал, подпишитесь, чтобы запустить бота.', reply_markup=keyboard)
#     else:
#         await bot.answer_callback_query(query.id)
#         try:
#             await bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
#         except MessageToDeleteNotFound:
#             pass
#         await start_bot(query.message, user_id)
#
#
# async def start_bot(message: types.Message, user_id: int):
#     request_db.add_request(user_id)
#     await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
#
#     if not user_db.user_exist(user_id):
#         user_db.add_user(user_id)
#
#         keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
#         keyboard.add(KeyboardButton('🤖 Услуги кодера'))
#         keyboard.add(KeyboardButton('⚙️ Статистика'))
#
#         await message.answer("👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/",
#                              reply_markup=keyboard)
#     else:
#         keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
#         keyboard.add(KeyboardButton('🤖 Услуги кодера'))
#         keyboard.add(KeyboardButton('⚙️ Статистика'))
#
#         await message.answer("👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/",
#                              reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "🤖 Услуги кодера")
async def coder_buttons(message: types.Message):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    buttons_text = message.text
    text = "<b>🦾 Понравился бот?</b> Может у тебя есть гениальная идея, но ты не знаешь как ее реализовать?\nТогда ты по адресу :)\n\n▫️ Мы поможем тебе перенести твои теоретические задумки на практический результат!\n\n➖ Создание телеграмм ботов\n➖ Различного вида сайты: лендинг, магазин, корпоративный сайт и то, что вроде как запрещено, но не для нас\n➖ Десктопный софт (чекеры, сортеры)\n➖ Мы привносим в вашу идею свой обширный опыт!\n\n▫️ 95% клиентов, которые работали со мной когда-либо - продолжают работать и по сей день, это говорит о многом!\n◾️ Пишите, обсудим детальнее вашу задачу и найдём лучший вариант!\n🔥 Связь: @Rare_c0de\n📍Канал: @rare_hood "
    photo_path = './hood_rare.jpg'
    photo = open(photo_path, 'rb')
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🗑 Убрать", callback_data="remove"))
    await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, reply_markup=markup)


@dp.message_handler(lambda message: message.text == "⚙️ Статистика")
async def statistic_buttons(message: types.Message):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    course_count = course_db.get_course_count()
    # request_count_today = request_db.get_request_count_today()
    # request_count_total = request_db.get_request_count_total()
    user_count = user_db.get_user_count()

    text = f"🕋 Курсов в базе данных: {course_count}\n🙎‍♂️ Пользователей в боте: {user_count}"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🗑 Убрать", callback_data="remove"))
    await bot.send_message(message.chat.id, text, reply_markup=markup)


@dp.callback_query_handler(lambda query: query.data == 'remove')
async def remove_message(query: types.CallbackQuery):
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)


# =====================================================================================================
# ====================================== ОБРАБОТКА ССЫЛКИ НА КУРС =====================================
# =====================================================================================================
async def send_wait_message(chat_id):
    message_text = '😉 Подожди, пожалуйста, сейчас я всё достану...'
    message = await bot.send_message(chat_id, message_text)
    dots = ['.  ', '.. ', '...']
    counter = 0
    while counter < 10:
        await asyncio.sleep(1)
        new_message_text = f'😉 Подожди, пожалуйста, сейчас я всё достану{dots[counter%3]}'
        if new_message_text != message_text:
            asyncio.create_task(bot.edit_message_text(new_message_text, chat_id, message.message_id))
            message_text = new_message_text
        counter += 1


@dp.message_handler()
async def message_handler(message: types.Message):
    global courses_per_day  # объявляем, что используем глобальную переменную
    user_id = message.from_user.id
    today = datetime.now().date()
    if user_id not in courses_per_day:
        courses_per_day[user_id] = [(today, 1)]
    else:
        if courses_per_day[user_id][-1][0] == today:
            if courses_per_day[user_id][-1][1] >= 5:
                await message.answer("Вы уже получили максимальное количество курсов за сегодня.")
                return
            else:
                courses_per_day[user_id][-1] = (today, courses_per_day[user_id][-1][1] + 1)
        else:
            courses_per_day[user_id].append((today, 1))

    if message.from_user and re.match(r'^https?://[\w\-\.~:/\?#\[\]@!\$&\'\(\)\*\+,;=%]+$', message.text):
        course_url = message.text
        channel_id = "-834856996"
        message_text = f"🔥 Пользователь @{message.from_user.username} ввел ссылку на курс:\n\n{course_url} "
        await bot.send_message(channel_id, message_text,)
        await send_wait_message(message.chat.id)
        course_info = course_db.get_url(course_url)
        if course_info:
            title, download_url = course_info[0], course_info[1]
            message_text = f"<b>💎 Курс доступен для скачивания 💎</b>\n\n<b>Название: {title}</b>\n\n\n<a href='{download_url}'>Скачать курс </a>"
            await message.answer(message_text, parse_mode="HTML")
        else:  # если сессия еще не авторизована, то выполняем авторизацию
            if not session.cookies.get_dict().get('xf_user'):
                # get csrf_token, site_key
                while True:
                    try:
                        response = session.get('https://s1.sharewood.co/login/')
                        soup = BeautifulSoup(response.content, "html.parser")
                        csrf_token = soup.find("input", {"name": "_xfToken", "type": "hidden"}).get("value")
                        site_key = soup.find("div", {'data-xf-init': "h-captcha"}).get("data-sitekey")
                        break
                    except api.exceptions.ApiError as e:
                        if e.error_code == "ERROR_RECAPTCHA_INVALID_SITEKEY":
                            continue
                        else:
                            raise e

                # captcha
                solver = hCaptchaProxyless()
                solver.set_verbose(1)
                solver.set_key(API_KEY)
                solver.set_website_url('https://s1.sharewood.co/login/')
                solver.set_website_key(site_key)
                g_response = solver.solve_and_return_solution()
                if g_response == 0:
                    return
                captcha_response = g_response
                data = {
                    "_xfToken": csrf_token,
                    "login": "hopawoc397@altpano.com",
                    "password": "ksdfj82347Hkd",
                    'g-recaptcha-response': captcha_response,
                    "h-captcha-response": captcha_response,
                    'remember': '1',
                }
                encoded_data = urlencode(data)
                headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://s1.sharewood.co',
                    'referer': 'https://s1.sharewood.co/login/',
                }
                response = session.post('https://s1.sharewood.co/login/login', data=encoded_data, headers=headers)
            while course_url:
                response = session.get(course_url)
                soup = BeautifulSoup(response.content, "html.parser")
                csrf_token = soup.find("input", {"name": "_xfToken", "type": "hidden"}).get("value")
                response = requests.get(course_url)
                html = response.text
                pattern = r'/posts/(\d+)/(reactions|share)'
                match = re.search(pattern, html)
                post_id = match.group(1)
                like_url = f"https://s1.sharewood.co/posts/{post_id}/react?reaction_id=1"
                payload = {
                    "reaction_id": "1",
                    "_xfWithData": "1",
                    "_xfToken": csrf_token,
                    "_xfResponseType": "json"
                }
                encoded_data = urlencode(payload)
                headers = {
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://s1.sharewood.co',
                    'referer': course_url,
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                }
                session.post(like_url, data=encoded_data, headers=headers)

                time.sleep(1)

                # Получаем инфо о курсе
                response = session.get(course_url)

                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find("h1", {"class": "p-title-value"}).text.strip()
                description = soup.find("div", {"class": "bbWrapper"}).text.strip()
                bb_code_block = soup.find('div', class_='bbCodeBlock bbCodeBlock--hide clike')

                content = bb_code_block.find('div', class_='bbCodeBlock-content')

                download_link = content.find('a')['href']

                course_db.add_link(course_url, title, download_link)

                message_text = f"<b>💎 Курс доступен для скачивания 💎</b>\n\n<b>Название: {title}</b>\n\n\n<a href='{download_link}'>👉🏻 Скачать курс  </a>"
                message_alerts = f"💎 Курс: <b>{title}</b>\n\n <b>➖ Выдан пользователю</b> @{message.from_user.username}"
                await message.answer(message_text, parse_mode="HTML")
                await bot.send_message(channel_id, message_alerts, parse_mode="HTML")

                await message.answer("<b>▫️ Что-бы запросить новый курс - просто пришли мне ссылку</b>")
                await message.delete()

                try:
                    next_message = await bot.wait_for('message', chat_id=message.chat.id)
                    course_url = next_message.text
                except TypeError:
                    course_url = None




# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
