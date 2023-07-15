# api_utils.py

import json
import os
import random
from typing import Tuple

import aiohttp
import requests
from datetime import datetime, timedelta, time
from aiogram import types
from sqlalchemy import select

from create_bot import bot
from db_models import Player
from settings import async_session_maker


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
        # request = requests.get(f"http://api.swgoh.gg/player/{i.ally_code}/gac-bracket/")
        #
        # if request.status_code == 200:
        #     data = request.json()
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

    result.append(f"Зареганных всего: {count_true}")
    result.append(f"Завтыкали: {count_false}")
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
    now = datetime.now()
    today = now.date()
    new_day_start = datetime.combine(today, time(int(os.environ.get("DAY_UPDATE_HOUR", "16")),
                                                 int(os.environ.get("DAY_UPDATE_MINUTES", "30"))))

    if now < new_day_start:
        new_day_start = new_day_start - timedelta(days=1)

    return new_day_start


async def get_players_list_from_ids(message: types.Message) -> Tuple[str, str]:
    """Возвращает список содержимого в ids.json"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'ids.json')
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
        await bot.send_message(message.chat.id, "Файл ids.json не найден.")


async def add_player_to_ids(message: types.Message) -> None:
    """Добавляет запись о пользователе в ids.json"""
    player_info = message.text.split(" ")
    if len(player_info) != 5:
        await bot.send_message(message.chat.id,
                               f"Неверный формат команды. Используйте: \n/add_player имя код_союзника тг_id тг_ник\n Все через один пробел.")
        return
    # имя игрока, код и ID телеграма и ник в телеграме
    player_name, ally_code, tg_id, tg_nic = player_info[1], player_info[2], player_info[3], player_info[4]

    file_path = os.path.join(os.path.dirname(__file__), '..', 'ids.json')
    if os.path.exists(file_path):
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        if len(data) >= 50:
            await bot.send_message(message.chat.id, f"Превышено число членов гильдии. Добавление невозможно!")
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

            await bot.send_message(message.chat.id, f"Игрок {player_name} был добавлен в список.")
    else:
        await bot.send_message(message.chat.id, "Файл ids.json не найден.")


async def delete_player_from_ids(message: types.Message):
    player_name = message.get_args()  # Получаем имя игрока
    if not player_name:
        await message.reply("Пожалуйста, предоставьте имя игрока.")
        return

    file_path = os.path.join(os.path.dirname(__file__), '../ids.json')

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
        await message.reply("Игрок с таким именем не найден.")
        return

    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)

    await bot.send_message(message.chat.id, f"Игрок {player_name} удален из списка.")


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


async def format_scores(sorted_scores, filter_points, total=True):
    # форматируем результат в нужный вид и сортируем по убыванию очков
    filtered_scores = [
        player for player in sorted_scores
        if filter_points is None or player[1] < filter_points
    ]
    reid_scores = [
        f"{i + 1}. {player[0]} {player[1]} купонов"
        for i, player in enumerate(filtered_scores)
    ]
    if total:
        reid_scores.append(f"Всего: {len(reid_scores)}")
    return reid_scores