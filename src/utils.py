# api_utils.py
import asyncio
import json
import os
import random
import re
from typing import Tuple, List

import aiohttp
import pytz
from datetime import datetime, timedelta, time
from aiogram import types, Bot
from sqlalchemy import select

from create_bot import bot
from db_models import Player
from settings import async_session_maker
from aiogram.utils.exceptions import ChatNotFound
import random as rn


async def gac_statistic() -> tuple:
    """Выдает статистику по игрокам зарегались на ВГ или нет."""
    new_day_start = get_new_day_start()
    async with async_session_maker() as session:
        query = await session.execute(
            select(Player).filter(
                Player.update_time >= new_day_start))
        players_list = query.scalars().all()
    result = []
    count_true = 0
    count_false = 0
    link_pre = 'https://swgoh.gg/p/'
    for i in players_list:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.swgoh.gg/player/{i.ally_code}/gac-bracket/") as request:
                if request.status == 200:
                    request.raise_for_status()
                    data = await request.json()

                    message = f"{i.name} зареган. Противники: \n"
                    bracket_players = data['data']['bracket_players']
                    temp_list = []

                    for j in bracket_players:
                        if j['player_name'] == i.name:
                            pass
                        else:
                            st = f"[{j['player_name']}]({link_pre}{j['ally_code']})"
                            temp_list.append(st)

                    message += ", ".join(temp_list)
                    result.append(message)
                    count_true += 1
                else:
                    result.append(f'{i.name} не зареган')
                    count_false += 1

    result.append(f"✅ Зареганных всего: {count_true}" if count_true == 50 else f"❗️ Зареганных всего: {count_true}")
    result.append("✅ Завтыкавших нет" if count_false == 0 else f"🚷 Завтыкали: {count_false}")
    st_1, st_2, st_3, st_4, st_5 = split_list(result)
    return f'\n{"-" * 30}\n'.join(st_1), f'\n{"-" * 30}\n'.join(st_2), f'\n{"-" * 30}\n'.join(
        st_3), f'\n{"-" * 30}\n'.join(st_4), f'\n{"-" * 30}\n'.join(st_5)


def split_list(input_list: list, parts: int = 5) -> list:
    """Возвращает вложенный список со списками равно поделенными"""
    length = len(input_list)
    return [input_list[i * length // parts: (i + 1) * length // parts]
            for i in range(parts)]


def get_new_day_start() -> datetime:
    """Возвращает начало нового дня установленного в .env файле (16:30 по умолчанию."""
    moscow_tz = pytz.timezone(os.environ.get('TIME_ZONE'))
    naive_now = datetime.now(moscow_tz)
    now = naive_now.replace(tzinfo=None)
    today = now.date()
    new_day_start = datetime.combine(today, time(int(os.environ.get("DAY_UPDATE_HOUR", "16")),
                                                 int(os.environ.get("DAY_UPDATE_MINUTES", "30"))))

    if now < new_day_start:
        new_day_start = new_day_start - timedelta(days=1)

    return new_day_start


async def get_players_list_from_ids(message: types.Message) -> Tuple[str, str]:
    """Возвращает список содержимого в ids.json"""
    file_path = os.path.join(os.path.dirname(__file__), '..', os.environ.get("IDS_JSON"))
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Перебираем список игроков и формируем строку
        msg_list = []
        for index, player in enumerate(data):
            for ally_code, info in player.items():
                msg = (
                    f"{index + 1}: {info['player_name']}\n"
                    f"Код союзника: {ally_code}\n"
                    f"ID: {info['tg_id']}\n"
                    f"TG_NIC: {info['tg_nic']}\n"
                    f"{'-' * 30}\n"
                )
                msg_list.append(msg)
        msg_list.append(f"Всего: {len(data)}")
        final_lst_1, final_lst_2 = split_list(msg_list, 2)  # hfpltkztv
        # Соединяем все сообщения в одну большую строку
        final_msg_1 = ''.join(final_lst_1)
        final_msg_2 = ''.join(final_lst_2)

        return final_msg_1, final_msg_2
    else:
        await bot.send_message(message.chat.id, "❌ Файл ids.json не найден.")


async def add_player_to_ids(message: types.Message, new_data: dict) -> None:
    """Добавляет запись о пользователе в ids.json"""

    # имя игрока, код и ID телеграма и ник в телеграме
    player_name, ally_code, tg_id, tg_nic = new_data['player_name'], new_data["ally_code"], new_data['tg_id'], new_data[
        'tg_nic']

    file_path = os.path.join(os.path.dirname(__file__), '..', os.environ.get("IDS_JSON"))
    if os.path.exists(file_path):
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        if len(data) >= 50:
            await bot.send_message(message.chat.id, f"❌Превышено число членов гильдии. Добавление невозможно!\n"
                                                    f"Команда отменена.")
        else:
            # Добавление нового игрока в список
            data.append({
                ally_code: {
                    "player_name": player_name,
                    "tg_id": tg_id,
                    "tg_nic": tg_nic
                }
            })

            # Запись обновленного списка в файл
            with open(file_path, "w") as json_file:
                json.dump(data, json_file, ensure_ascii=False)

            await bot.send_message(message.chat.id, f"✅ Игрок {player_name} был добавлен в список.\n\n"
                                                    f"⚠️ После добавления проверьте полный список, "
                                                    f"что все правильно добавилось\n"
                                                    f"Если нет, то удалите и добавьте заново.")
    else:
        await bot.send_message(message.chat.id, "❌ Файл ids.json не найден.")


async def delete_player_from_ids(message: types.Message, player_name):
    file_path = os.path.join(os.path.dirname(__file__), f'../{os.environ.get("IDS_JSON")}')

    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    player_found = False  # флаг, чтобы отслеживать, найден ли игрок

    for index, player in enumerate(data):
        for ally_code, info in player.items():
            if info["player_name"] == player_name:
                del data[index]  # Удаляем запись игрока
                player_found = True  # отмечаем, что игрок найден
                break

        if player_found:
            break
    else:
        await message.reply("❌ Игрок с таким именем не найден.")
        return

    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)

    await bot.send_message(message.chat.id, f"✅ Игрок {player_name} удален из списка.")


async def send_photo_message(tg_id: str or int, caption_text: str):
    # указываем путь к вашей папке
    media_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')

    # получаем список всех файлов в каталоге
    files = os.listdir(media_folder)

    # выбираем случайный файл
    random_file = random.choice(files)

    # формируем полный путь до файла
    photo_path = os.path.join(media_folder, random_file)

    with open(photo_path, 'rb') as photo:
        # проверяем расширение файла
        if random_file.lower().endswith('.gif'):
            await bot.send_animation(tg_id, photo, caption=caption_text)
        else:
            await bot.send_photo(tg_id, photo, caption=caption_text)


async def format_scores(sorted_scores, filter_points, total=True, powers=False):
    # форматируем результат в нужный вид и сортируем по убыванию очков
    filtered_scores = [
        player for player in sorted_scores
        if filter_points is None or player[1] < filter_points
    ]
    if powers:
        reid_scores = [
            f"{i + 1}. {player[0]} {player[1]} гм"
            for i, player in enumerate(filtered_scores)
        ]
    else:
        reid_scores = [
            f"{i + 1}. {player[0]} {player[1]} купонов"
            for i, player in enumerate(filtered_scores)
        ]
    if total:
        reid_scores.append(f"Всего: {len(reid_scores)}")
    return reid_scores


async def check_guild_players(message: types.Message):
    is_guild_member = message.conf.get('is_guild_member', False)
    if is_guild_member:
        # try:
        file_path = os.path.join(os.path.dirname(__file__), f'../{os.environ.get("IDS_JSON")}')
        with open(file_path, 'r', encoding='utf-8') as file:
            players = json.load(file)

        for player in players:
            player_info = list(player.values())[0]
            print(player_info)
            player_tg_id = player_info['tg_id']
            player_tg_nic = player_info['tg_nic']
            player_name = player_info['player_name']
            try:
                if player_tg_id is None or player_tg_id == 'null' or len(player_tg_id) < 2:
                    await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                                           f"⚠️ Игрок: {player_name}, не зарегистрировал свой ТГ ID")
                    await asyncio.sleep(3)
                elif player_tg_nic is None or player_tg_nic == 'null' or len(player_tg_nic) < 2:
                    await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                                           f"⚠️ У игрока: {player_name}, не создан или не добавлен ТГ ник")
                    await asyncio.sleep(3)
                else:
                    sent_message = await bot.send_message(player_tg_id,
                                                          f"✅ Проверка. Не обращай внимания. Проводится тестирование.")
                    await bot.delete_message(sent_message.chat.id, sent_message.message_id)
                    await asyncio.sleep(3)
            except ChatNotFound:
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                                       f"❌ Игрок: {player_name} @{player_tg_nic}, не нажал СТАРТ или был введен неправильны ID")
                await asyncio.sleep(3)
        await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                               f"✅ Проверка завершена.")

    # except Exception as e:
    #     await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


def get_localized_datetime(timestamp_millis: int, timezone_str: str = None) -> datetime:
    """Преобразует timestamp из миллисекунд в datetime с учетом временной зоны"""

    timestamp_seconds = timestamp_millis / 1000  # преобразуем в секунды
    date_object = datetime.utcfromtimestamp(timestamp_seconds)

    # Если временная зона не указана, возвращаем время в UTC
    if timezone_str is None:
        return date_object

    # Создаём объект временной зоны
    time_z = pytz.timezone(timezone_str)

    # Получаем текущее смещение от UTC в часах
    utc_offset_hours = time_z.utcoffset(date_object).total_seconds() / 3600

    # Добавляем это смещение к нашему времени
    date_object = date_object + timedelta(hours=utc_offset_hours)

    return date_object


async def delete_db_player_data(val):
    """Безвозвратно удаляет все записи связанные с игроком из БД"""
    async with async_session_maker() as session:
        player_records = await session.execute(
            select(Player).filter_by(name=val))
        player_records = player_records.scalars().all()
        if len(player_records) == 0:
            try:
                async with async_session_maker() as session:
                    player_records = await session.execute(
                        select(Player).filter_by(ally_code=int(val)))
                    player_records = player_records.scalars().all()
                    if len(player_records) == 0:
                        await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                                               f"❌ Игрок с значением {val} отсутствует\n"
                                               f"Проверьте правильность написания имени или кода союзника")
                        return
            except Exception as e:
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), f"❌ Игрок с значением {val} отсутствует\n"
                                                                          f"Проверьте правильность написания имени или кода союзника")
                return
    player_name: str = player_records[0].name
    for player in player_records:
        async with async_session_maker() as session:
            await session.delete(player)
            await session.commit()

    return player_name


async def send_points_message(player: Player, speach_list: list, rus: bool):
    try:
        await send_photo_message(player.tg_id,
                                 f"{player.name}, {rn.choice(speach_list)} {player.reid_points} {'купонов' if rus else 'points'}.")
        print(f"{player.name} энка")
    except ChatNotFound as e:
        await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                               f"❌ У {player.name} не подключена телега к чату.")


async def get_player_by_name_or_nic(player_name: str) -> Player:
    """Находит игрока в базе по тг нику или по имени акка"""
    new_day_start = get_new_day_start()  # начало нового дня
    async with async_session_maker() as session:
        # Первый запрос: попытка найти по Player.name
        query = await session.execute(
            select(Player).filter(Player.update_time >= new_day_start, Player.name == player_name)
        )
        player = query.scalars().first()

        # Если игрок не найден по имени, попытка найти по tg_nic
        if not player:
            query = await session.execute(
                select(Player).filter(Player.update_time >= new_day_start, Player.tg_nic == player_name)
            )
            player = query.scalars().first()
        return player


async def get_end_date():
    now = get_new_day_start()
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, now.hour, now.minute) - timedelta(days=1)
    else:
        end = datetime(now.year, now.month + 1, 1, now.hour, now.minute) - timedelta(days=1)
    return end


async def is_admin(bot: Bot, user_id, chat_id) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.is_chat_admin() or member.is_chat_creator()
    except:
        member = await bot.get_chat_member(chat_id.id, user_id.id)
        return member.is_chat_admin() or member.is_chat_creator()


async def get_monthly_records(player_name: str) -> List[Player]:
    async with async_session_maker() as session:
        # Получить все записи, отсортированные по времени обновления
        query = select(Player).order_by(Player.update_time).filter_by(name=player_name)
        result = await session.execute(query)
        all_records = result.scalars().all()

        # Если нет записей, возвращаем пустой список
        if not all_records:
            return []

        # Начинаем с самой ранней записи
        monthly_records = [all_records[0]]

        # Ищем запись для первого числа каждого последующего месяца
        current_date = all_records[0].update_time
        for record in all_records:
            if record.update_time.month != current_date.month or record.update_time.year != current_date.year:
                monthly_records.append(record)
                current_date = record.update_time

        return monthly_records


async def is_super_admin(tg_id: str):
    """Проверяет суперадмин ли пользователь"""
    env_members = os.environ.get("SUPER_ADMINS")
    eng_members_list = list(map(int, env_members.split(",")))
    if tg_id in eng_members_list:
        return True
    return False


async def is_member_admin_super(call: types.CallbackQuery = None, super_a: bool = False, message: types.Message = None):
    if message:
        is_guild_member = message.conf.get('is_guild_member', False)
        admin = await is_admin(bot, message.from_user, message.chat)
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        tg_id = member['user']['id']
        super_admin = await is_super_admin(tg_id)
        if super_a:
            return is_guild_member, admin, super_admin
        return is_guild_member, admin
    is_guild_member = call.message.conf.get('is_guild_member', False)
    admin = await is_admin(bot, call.from_user, call.message.chat)
    member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    tg_id = member['user']['id']
    super_admin = await is_super_admin(tg_id)
    if super_a:
        return is_guild_member, admin, super_admin
    return is_guild_member, admin


def is_valid_name(name):
    # Регулярное выражение, которое проверяет, состоит ли строка только из букв и цифр
    return bool(re.match('^[a-zA-Z0-9_-]*$', name))


async def send_id(bot, message: types.Message):
    # Получить путь к текущему файлу
    current_file_path = os.path.realpath(__file__)
    # Получить путь к каталогу текущего файла
    current_dir_path = os.path.dirname(current_file_path)
    # Сформировать путь к ids.json
    ids_file_path = os.path.join(current_dir_path, '..', os.environ.get('IDS_JSON'))

    # Загрузить ids.json в память
    with open(ids_file_path) as f:
        guild_members = json.load(f)

    my_chat_id = int(os.environ.get('MY_ID'))
    user_id = str(message.from_user.id)

    # Найти player_name по user_id
    player_name = None
    for dictionary in guild_members:
        for player_data in dictionary.values():
            if player_data.get('tg_id') == user_id:
                player_name = player_data.get('player_name')
                break

    if player_name:
        await bot.send_message(my_chat_id, f"ID пользователя: {user_id}, Имя игрока: {player_name}")
    else:
        await bot.send_message(my_chat_id, f"ID пользователя: {user_id} не найден в guild_members.")
