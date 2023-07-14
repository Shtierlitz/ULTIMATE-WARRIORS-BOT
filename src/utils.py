# api_utils.py
import io
import os
import requests
# from create_bot import session
from datetime import datetime, timedelta, time

from aiogram import types
from sqlalchemy import select, or_

from create_bot import bot
from db_models import Player
from settings import async_session_maker
from plotly import graph_objs as go
from plotly import io as pio


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


async def get_month_player_graphic(message: types.Message, player_name: str) -> io.BytesIO or None:
    # Извлечение данных из базы данных
    async with async_session_maker() as session:
        query = await session.execute(
            select(Player).filter(or_(Player.name == player_name, Player.tg_nic == player_name))
        )
        player_data = query.scalars().all()

    # Проверка, есть ли данные
    if not player_data:
        await bot.send_message(message.chat.id,
                               text=f"Неверно введено имя \"{player_name}\". Попробуйте проверить правильность написания")
        return

    # Подготовка данных для построения графика
    data = sorted([(player.update_time, int(player.reid_points)) for player in player_data])
    update_times, reid_points = zip(*data)

    # Построение графика
    fig = go.Figure(data=go.Scatter(
        x=update_times,
        y=reid_points,
        mode='lines+markers+text',
        text=reid_points,
        textposition='top center'))

    fig.update_layout(
        title=f'Reid Points Over Month for {player_name}',
        xaxis_title='Update Time',
        yaxis_title='Reid Points',
        yaxis=dict(
            range=[-100, 700],
            tickmode='linear',
            tick0=0,
            dtick=50
        )
    )

    # Сохранение графика в виде файла изображения
    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png')
    buf.seek(0)

    return buf
