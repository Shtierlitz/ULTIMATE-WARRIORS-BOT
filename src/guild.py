# src/guild.py
import io
import os

import pytz
import requests
from sqlalchemy import func, delete, select

# from create_bot import session
from settings import async_session_maker
from datetime import datetime, timedelta, time

from db_models import Player, Guild
from pytz import timezone
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta
from src.errors import Status404Error, DatabaseBuildError
from src.utils import get_new_day_start

import plotly.graph_objects as go
import plotly.io as pio

load_dotenv()

utc_tz = timezone('UTC')

tz = str(os.environ.get("TIME_ZONE"))
time_tz = timezone(tz)

API_LINK = f"{os.environ.get('API_HOST')}:{os.environ.get('API_PORT')}"
GUILD_POST_DATA = {
    "payload": {
        "guildId": os.environ.get("GUILD_ID"),
        "includeRecentGuildActivityInfo": True
    },
    "enums": False
}


class GuildData:

    @staticmethod
    def get_guild_data() -> dict:
        """Собирает и возвращает данные про гильдию (только полезные)"""
        result = {}
        try:
            comlink_request = requests.post(f"{API_LINK}/guild", json=GUILD_POST_DATA)
            comlink_request.raise_for_status()
            data = comlink_request.json()

            result['name'] = data['guild']['profile']['name']
            result['guild_id'] = data['guild']['profile']['id']
            result['credo'] = data['guild']['profile']['externalMessageKey']
            result['galactic_power'] = data['guild']['profile']['guildGalacticPower']
            result['required_level'] = data['guild']['profile']['levelRequirement']
            result['total_members'] = data['guild']['profile']['memberCount']
            result['guild_reset_time'] = data['guild']['nextChallengesRefresh']

        except requests.exceptions.HTTPError:
            raise Status404Error("There was an error getting comlink guild data.")
        return result

    async def __set_guild_attributes(self, guild: Guild, data):
        """Промежуточная функция. назначает атрибуты модели гильдии"""
        guild.name = data['name']
        guild.guild_id = data['guild_id']
        guild.credo = data['credo']
        guild.total_members = data['total_members']
        guild.required_level = data['required_level']
        guild.galactic_power = data['galactic_power']

        # преобразовываем время в вашу временную зону и удаляем информацию о временной зоне перед записью в базу данных
        now = datetime.now(pytz.UTC).astimezone(time_tz).replace(tzinfo=None)
        guild.last_db_update_time = now

        timestamp_seconds = int(data['guild_reset_time']) / 1000  # преобразуем в секунды
        date_object = datetime.fromtimestamp(timestamp_seconds, tz=pytz.utc)
        guild.guild_reset_time = date_object.replace(tzinfo=None)

        return guild

    async def build_db(self):
        """Строит базу данных и собранных данных"""
        try:
            data = self.get_guild_data()
            new_day_start = get_new_day_start()
            async with async_session_maker() as session:
                async with session.begin():
                    guild_data_today = (await session.execute(
                        select(Guild).where(Guild.last_db_update_time >= new_day_start)
                    )).scalar_one_or_none()

                if guild_data_today:
                    # Обновляем старую запись гильдии
                    print('guild_old')
                    await self.__set_guild_attributes(guild_data_today, data)
                    await session.commit()
                else:
                    # Добавляем новую запись гильдии
                    new_guild = await self.__set_guild_attributes(Guild(), data)
                    session.add(new_guild)
                    await session.commit()
                    print('guild_new')

                    # Удаление записей старше месяца
                year_old_date = datetime.now() - timedelta(days=365)
                (await session.execute(
                    delete(Guild).where(Guild.last_db_update_time < year_old_date)
                ))
                await session.commit()
        except Exception as e:
            raise DatabaseBuildError(f"An error occurred while building the Guild database: {e}") from e

    @staticmethod
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
        x_values = [guild.last_db_update_time.strftime("%d-%m-%Y") for guild in guild_data]
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
            title=f'Raise galactic power per {period}',
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


        buf = io.BytesIO()
        pio.write_image(fig, buf, format='png')
        buf.seek(0)

        return buf



