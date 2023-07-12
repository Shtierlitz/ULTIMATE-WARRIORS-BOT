# src/guild.py


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

from src.errors import Status404Error, DatabaseBuildError
from src.utils import get_new_day_start

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
        guild.last_db_update_time = datetime.now(pytz.UTC).replace(tzinfo=None)
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
                    print('guild_today')
                    await self.__set_guild_attributes(guild_data_today, data)
                    await session.commit()
                else:
                    # Добавляем новую запись гильдии
                    new_guild = await self.__set_guild_attributes(Guild(), data)
                    session.add(new_guild)
                    await session.commit()

                    # Удаление записей старше месяца
                month_old_date = datetime.now() - timedelta(days=30)
                (await session.execute(
                    delete(Guild).where(Guild.last_db_update_time < month_old_date)
                ))
                await session.commit()
        except Exception as e:
            raise DatabaseBuildError(f"An error occurred while building the Guild database: {e}") from e
