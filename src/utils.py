# api_utils.py


import os
import requests
# from create_bot import session
from datetime import datetime, timedelta, time

from sqlalchemy import select

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
        request = requests.get(f"http://api.swgoh.gg/player/{i.ally_code}/gac-bracket/")

        if request.status_code == 200:
            data = request.json()

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
