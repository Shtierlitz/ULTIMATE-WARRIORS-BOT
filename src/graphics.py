# src/graphics.py

import json
import os
from db_models import Player, Guild
from settings import async_session_maker
from plotly import graph_objs as go
from plotly import io as pio
import io

from dateutil.relativedelta import relativedelta
from sqlalchemy import select

from src.utils import get_new_day_start, get_monthly_records
from datetime import datetime


async def get_player_gp_graphic(player_name, period):
    """Создает график галактической мощи игрока по месяцу или году"""
    new_day_start = get_new_day_start()
    if period == "month":
        one_month_ago = new_day_start - relativedelta(months=1)  # Вычислить дату один месяц назад
        async with async_session_maker() as session:
            player_data = await session.execute(
                select(Player).filter_by(name=player_name).filter(
                    Player.update_time >= one_month_ago))  # Использовать эту дату в фильтре
            player_data = player_data.scalars().all()
    else:
        one_year_ago = new_day_start - relativedelta(months=12)
        async with async_session_maker() as session:
            # Получаем все данные для игрока
            stmt = select(Player).filter(Player.name == player_name, Player.update_time >= one_year_ago)

            all_data = await session.execute(stmt)
            all_data = all_data.scalars().all()

            # Сортируем данные по дате обновления
            all_data.sort(key=lambda x: x.update_time)

            # Берем первую запись для каждого месяца
            player_data = []
            current_month = None
            for record in all_data:
                if record.update_time.month != current_month:
                    player_data.append(record)
                    current_month = record.update_time.month

    # Создаем график с использованием plotly
    x_values = [
        player.update_time if i == len(player_data) - 1 else player.update_time.replace(hour=0, minute=0, second=0,
                                                                                        microsecond=0)
        for i, player in enumerate(player_data)
    ]
    y_values = [player.galactic_power for player in player_data]
    # Сначала объединяем списки в список кортежей
    data = list(zip(x_values, y_values))

    # Сортируем список кортежей по дате
    data.sort(key=lambda x: x[0])
    if period == "month":
        data.pop()

    # Разделяем отсортированный список кортежей обратно на два списка
    x_values, y_values = zip(*data)

    fig = go.Figure(data=go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        textposition='top center',
    ))

    fig.update_layout(
        width=len(x_values) * 100 if len(x_values) > 10 else 1200,
        title=f'<b>{player_name}\'s</b> galactic power per <b>{period}</b>',
        xaxis_title='Update Time',
        yaxis_title='Galactic Power',
    )

    # Вычисляем разницу между самым поздним и самым ранним значением
    difference_gp = y_values[-1] - y_values[0]

    # Добавляем аннотацию с этой разницей
    fig.add_annotation(
        xref='paper', x=1, yref='paper', y=0,
        text=f"Total difference: {difference_gp:,}",
        showarrow=False,
        font=dict(
            size=14,
            color="#ffffff"
        ),
        align="right",
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
    )

    fig.add_annotation(
        xref='paper', x=0, yref='paper', y=1,
        text=f"Last value: {y_values[-1]:,}",
        showarrow=False,
        font=dict(
            size=14,
            color="#ffffff"
        ),
        align="right",
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#666bff",
        opacity=0.8
    )

    fig.update_xaxes(
        tickangle=45,
        tickvals=x_values,
        tickformat="%d-%m"
    )

    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png')
    buf.seek(0)

    return buf


async def get_month_player_graphic(player_name: str) -> io.BytesIO or None:
    """Создает график энки игрока за месяц"""

    file_path = os.path.join(os.path.dirname(__file__), '..', os.environ.get("IDS_JSON"))
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as json_file:
            data = json.load(json_file)
    # Ищем player_name в data и берем связанный с ним player_code, если находим
    ally_code = None
    for dictionary in data:
        for target_ally_code, player_info in dictionary.items():
            if player_info.get('tg_nic') == player_name or player_info.get('player_name') == player_name:
                ally_code = target_ally_code
                break
    # Извлечение данных из базы данных

    if ally_code:
        async with async_session_maker() as session:
            # Если нашли player_code в data, используем его для поиска в базе данных
            query = await session.execute(
                select(Player).filter(Player.ally_code == int(ally_code))
            )
            # Иначе ищем по имени игрока, как раньше
            player_data = query.scalars().all()
    else:
        player_data = None

    # Проверка, есть ли данные
    if not player_data:
        return

    data = [(player.update_time.replace(hour=0, minute=0, second=0, microsecond=0) if i != len(
        player_data) - 1 else player.update_time, int(player.reid_points))
            for i, player in enumerate(player_data)]

    data.sort(key=lambda x: x[0])
    update_times, reid_points = zip(*data)

    # Построение графика
    fig = go.Figure(data=go.Scatter(
        x=update_times,
        y=reid_points,
        mode='lines+markers+text',
        text=reid_points,
        textposition='top center'))

    fig.update_layout(
        width=len(update_times) * 100 if len(update_times) > 10 else 1200,
        title=f'<b>Reid Points</b> Over Month for <b>{player_name}</b>',
        xaxis_title='Update Time',
        yaxis_title='Reid Points',
        yaxis=dict(
            range=[-40, 640],
            tickmode='linear',
            tick0=0,
            dtick=50
        )
    )

    fig.update_xaxes(
        tickangle=45,
        nticks=len(update_times),
        tickformat="%d-%m"
    )

    # Сохранение графика в виде файла изображения
    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png')
    buf.seek(0)

    return buf


async def get_guild_galactic_power(period: str) -> io.BytesIO:
    """Создает график роста ГМ гильдии за месяц или за год"""
    new_day_start = get_new_day_start()
    if period == 'month':
        one_month_ago = new_day_start - relativedelta(months=1)  # Вычислить дату один месяц назад
        async with async_session_maker() as session:
            guild_data = await session.execute(
                select(Guild).filter(
                    Guild.last_db_update_time >= one_month_ago))  # Использовать эту дату в фильтре
            guild_data = guild_data.scalars().all()
    else:
        one_year_ago = new_day_start - relativedelta(months=12)
        async with async_session_maker() as session:
            # Получаем все данные для игрока
            stmt = select(Guild).filter(Guild.last_db_update_time >= one_year_ago)

            all_data = await session.execute(stmt)
            all_data = all_data.scalars().all()

            # Сортируем данные по дате обновления
            all_data.sort(key=lambda x: x.last_db_update_time)

            # Берем первую запись для каждого месяца
            guild_data = []
            current_month = None
            for record in all_data:
                if record.last_db_update_time.month != current_month:
                    guild_data.append(record)
                    current_month = record.last_db_update_time.month

    # Создаем график с использованием plotly
    x_values = [guild.last_db_update_time.replace(hour=0, minute=0, second=0, microsecond=0) for guild in
                guild_data]
    y_values = [guild.galactic_power for guild in guild_data]

    # Сначала объединяем списки в список кортежей
    data = list(zip(x_values, y_values))

    # Сортируем список кортежей по дате
    data.sort(key=lambda x: x[0])
    if period == "month":
        data.pop()

    # Разделяем отсортированный список кортежей обратно на два списка
    x_values, y_values = zip(*data)

    difference_gp = int(y_values[-1]) - int(y_values[0])

    fig = go.Figure(data=go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        textposition='top center'))

    fig.update_layout(
        width=len(x_values) * 100 if len(x_values) > 10 else 1200,
        title=f'Raise <b>Guild</b> galactic power per <b>{period}</b>',
        xaxis_title='Update Time',
        yaxis_title='Galactic Power',

    )

    # Добавляем аннотацию с этой разницей
    fig.add_annotation(
        xref='paper', x=1, yref='paper', y=0,
        text=f"Total difference: {difference_gp:,}",
        showarrow=False,
        font=dict(
            size=14,
            color="#ffffff"
        ),
        align="right",
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
    )

    fig.add_annotation(
        xref='paper', x=0, yref='paper', y=1,
        text=f"Last value: {int(y_values[-1]):,}",
        showarrow=False,
        font=dict(
            size=14,
            color="#ffffff"
        ),
        align="right",
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#666bff",
        opacity=0.8
    )

    fig.update_xaxes(
        tickangle=45,
        tickvals=x_values,
        tickformat="%d-%m"
    )

    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png')
    buf.seek(0)

    return buf


async def get_player_rank_graphic(player_name: str, period: str, is_fleet: bool = None) -> io.BytesIO or None:
    new_day_start = datetime.now()
    if period == "month":
        one_month_ago = new_day_start - relativedelta(months=1)  # Вычислить дату один месяц назад
        async with async_session_maker() as session:
            player_data = await session.execute(
                select(Player).filter_by(name=player_name).filter(
                    Player.update_time >= one_month_ago))  # Использовать эту дату в фильтре
            player_data = player_data.scalars().all()
    else:
        player_data = await get_monthly_records(player_name)

    if not player_data:
        return None

        # Подготовка данных для построения графика
    if is_fleet:
        rank_data = [
            (player.update_time.replace(hour=0, minute=0, second=0, microsecond=0), player.fleet_arena_rank) for
            player in player_data]
    else:
        rank_data = [(player.update_time.replace(hour=0, minute=0, second=0, microsecond=0), player.arena_rank) for
                     player in player_data]

    rank_data.sort(key=lambda x: x[0])  # Сортируем по дате
    update_times, ranks = zip(*rank_data)

    # Построение графика
    fig = go.Figure(data=go.Scatter(
        x=update_times,
        y=ranks,
        mode='lines+markers+text',
        text=ranks,
        textposition='top center'))

    fig.update_layout(
        width=len(update_times) * 100 if len(update_times) > 10 else 1200,
        title=f'<b>{player_name}\'s Arena Rank</b> Over <b>{period.capitalize()}</b>' if not is_fleet else f'<b>{player_name}\'s Fleet Arena Rank</b> Over <b>{period.capitalize()}</b>',
        xaxis_title='Update Time',
        yaxis_title='Rank',
        yaxis=dict(
            dtick=10,
            autorange="reversed"  # добавьте эту строку
        )
    )

    fig.update_xaxes(
        tickangle=45,
        nticks=len(update_times),
        tickformat="%d-%m"
    )

    # Сохранение графика в виде файла изображения
    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png')
    buf.seek(0)

    return buf
