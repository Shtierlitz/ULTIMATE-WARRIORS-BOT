# src/guild.py
import logging
import os

import aiohttp
import pytz
import requests
from sqlalchemy import delete, select

from settings import logger
from settings import async_session_maker
from datetime import datetime, timedelta

from db_models import Guild
from pytz import timezone
from dotenv import load_dotenv

from src.errors import Status404Error, DatabaseBuildError
from src.utils import get_new_day_start, get_localized_datetime


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
    async def get_guild_data(self) -> dict:
        """Собирает и возвращает данные про гильдию (только полезные)"""
        result = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_LINK}/guild", json=GUILD_POST_DATA) as comlink_request:
                    comlink_request.raise_for_status()
                    data = await comlink_request.json()

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

        guild.guild_reset_time = get_localized_datetime(int(data['guild_reset_time']), str(os.environ.get('TIME_ZONE')))

        return guild

    async def build_db(self):
        """Строит базу данных и собранных данных"""
        try:
            data = await self.get_guild_data()
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
    async def get_latest_guild_data():
        new_day_start = get_new_day_start()
        async with async_session_maker() as session:
            async with session.begin():
                guild_data_today = (await session.execute(
                    select(Guild).where(Guild.last_db_update_time >= new_day_start)
                )).scalar_one_or_none()
        datetime_object = guild_data_today.guild_reset_time
        time_string = datetime_object.strftime("%H:%M")
        return [
            f"Name: {guild_data_today.name}",
            f"Guild ID: {guild_data_today.guild_id}",
            f"Credo: {guild_data_today.credo}",
            f"Galactic Power: {guild_data_today.galactic_power}",
            f"Required Level: {guild_data_today.required_level}",
            f"Total Members: {guild_data_today.total_members}",
            f"Guild Reset Time: {time_string}",
            f"Time zone: {os.environ.get('TIME_ZONE')}",
            f"Last DB Update Time: {guild_data_today.last_db_update_time}"
        ]
