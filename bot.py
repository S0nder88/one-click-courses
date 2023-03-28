import asyncio
import datetime
import re
import requests
from urllib.parse import urlencode

from aiogram.utils import executor
from bs4 import BeautifulSoup

import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.bot import api
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, message_id, message

from anticaptchaofficial.hcaptchaproxyless import *
from sqlite import UserDB, CourseDB, RequestDB

import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
CAPTCHA_API_KEY = "API KEY"

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


# Определяем функцию для обработки команды /alerts
@dp.message_handler(commands=['alerts'])
async def send_alerts(message: types.Message):
    # Проверяем, является ли пользователь администратором
    if message.from_user.id not in admins:
        await message.answer("Вы не являетесь администратором.")
        return

    # Получаем список пользователей
    users = user_db.get_all_users()

    # Получаем медиа-контент, если он есть
    media = None
    if message.photo:
        media = [types.InputMediaPhoto(media=photo.file_id) for photo in message.photo]
    elif message.video:
        media = [types.InputMediaVideo(media=video.file_id) for video in message.video]
    elif message.animation:
        media = [types.InputMediaAnimation(media=animation.file_id) for animation in message.animation]

    # Отправляем сообщение каждому пользователю
    for user in users:
        try:
            if media:
                await bot.send_media_group(chat_id=user.id, media=[types.InputMediaPhoto(media=media)],
                                           caption=message.text[len('/alerts '):])
            else:
                await bot.send_message(chat_id=user.id, text=message.text[len('/alerts '):])

        except Exception as e:
            print(f"Failed to send message to user {user.id}: {str(e)}")

    await message.answer(f"Рассылка завершена. Отправлено сообщений: {len(users)}")


@dp.message_handler(commands=['start'])
async def start_handler(message: aiogram.types.Message):
    request_db.add_request(message.from_user.id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    user_id = message.from_user.id
    chat_id = '-1001735705501'
    member = await bot.get_chat_member(chat_id, user_id)
    if member.status == 'left':
        # Если пользователь не подписан на канал, отправляем сообщение с инлайн кнопкой для подписки
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='Подписаться на канал', url='https://t.me/rare_hood'))
        keyboard.add(InlineKeyboardButton(text='🔍 Проверить подписку', callback_data='check_subscription'))
        await message.answer(f"Для использования бота, пожалуйста, подпишитесь на канал.", reply_markup=keyboard)
    else:
        if not user_db.user_exist(user_id):
            user_db.add_user(user_id)

            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton('🤖 Услуги кодера'))
            keyboard.add(KeyboardButton('⚙️ Статистика'))

            await message.answer("👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/",
                                 reply_markup=keyboard)

            chatt_id = '-834856996'
            username = message.from_user.username
            text = f"➖ @{username} - новый пользователь"
            await bot.send_message(chatt_id, text)

        else:
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton('🤖 Услуги кодера'))
            keyboard.add(KeyboardButton('⚙️ Статистика'))

            await message.answer("👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/",
                                 reply_markup=keyboard)


@dp.callback_query_handler(lambda query: query.data == 'check_subscription')
async def check_subscription_handler(query: types.CallbackQuery):
    user_id = query.from_user.id
    chat_id = '-1001735705501'
    member = await bot.get_chat_member(chat_id, user_id)
    if member.status == 'left':
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='Подписаться на канал', url='https://t.me/rare_hood'))
        await bot.send_message(chat_id=query.message.chat.id, text='Вы не подписаны на канал, подпишитесь, чтобы запустить бота.', reply_markup=keyboard)
    else:
        await bot.answer_callback_query(query.id)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
        except MessageToDeleteNotFound:
            pass
        await start_bot(query.message, user_id)


async def start_bot(message: types.Message, user_id: int):
    request_db.add_request(user_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    if not user_db.user_exist(user_id):
        user_db.add_user(user_id)

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('🤖 Услуги кодера'))
        keyboard.add(KeyboardButton('⚙️ Статистика'))

        await message.answer("👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/",
                             reply_markup=keyboard)

        chatt_id = '-834856996'
        username = message.from_user.username
        text = f"➖ @{username} - новый пользователь"
        await bot.send_message(chatt_id, text)

    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('🤖 Услуги кодера'))
        keyboard.add(KeyboardButton('⚙️ Статистика'))

        await message.answer("👋 Пришли ссылку на курс с этого сайта:\n\nhttps://s1.sharewood.co/",
                             reply_markup=keyboard)


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
            if courses_per_day[user_id][-1][1] >= 3:
                await message.answer("Вы уже получили максимальное количество курсов за сегодня.")
                return
            else:
                courses_per_day[user_id][-1] = (today, courses_per_day[user_id][-1][1] + 1)
        else:
            courses_per_day[user_id].append((today, 1))

    if message.from_user and re.match(r'^https?://[\w\-\.~:/\?#\[\]@!\$&\'\(\)\*\+,;=%]+$', message.text):
        course_url = message.text
        channel_id = "-834856996"
        message_text = f"🔥 Пользователь @{message.from_user.username} ввел ссылку на курс "
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
                solver.set_key(CAPTCHA_API_KEY)
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
                await message.answer(message_text, parse_mode="HTML")

                await message.answer("<b>▫️ Что-бы запросить новый курс - просто пришли мне ссылку</b>")
                await message.delete()

                try:
                    next_message = await dp.bot.wait_for('message', chat_id=message.chat.id)
                    course_url = next_message.text
                except TypeError:
                    course_url = None


# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
