# src/guild.py


import os

import requests
from sqlalchemy import func

from create_bot import session
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

            result['guild_id'] = data['guild']['profile']['id']
            result['name'] = data['guild']['profile']['name']
            result['credo'] = data['guild']['profile']['externalMessageKey']
            result['total_members'] = data['guild']['profile']['memberCount']
            result['required_level'] = data['guild']['profile']['levelRequirement']
            result['galactic_power'] = data['guild']['profile']['guildGalacticPower']
            result['guild_reset_time'] = data['guild']['nextChallengesRefresh']

        except requests.exceptions.HTTPError:
            raise Status404Error("There was an error getting comlink guild data.")
        return result

    def __set_guild_attributes(self, guild: Guild, data):
        """Промежуточная функция. назначает атрибуты модели гильдии"""
        guild.name = data['name']
        guild.guild_id = data['guild_id']
        guild.credo = data['credo']
        guild.total_members = data['total_members']
        guild.required_level = data['required_level']
        guild.galactic_power = data['galactic_power']
        guild.last_db_update_time = datetime.now(time_tz)

        timestamp = int(data['guild_reset_time'])
        guild_reset_time_utc = datetime.fromtimestamp(timestamp).replace(tzinfo=utc_tz)
        guild.guild_reset_time = guild_reset_time_utc

        return guild

    def build_db(self):
        """Строит базу данных и собранных данных"""
        try:
            data = self.get_guild_data()
            new_day_start = get_new_day_start()

            guild_data_today = session.query(Guild).filter(
                Guild.last_db_update_time >= new_day_start).first()

            if guild_data_today:
                # Обновляем старую запись гильдии
                print('guild_today')
                self.__set_guild_attributes(guild_data_today, data)
                session.commit()
            else:
                # Добавляем новую запись гильдии
                new_guild = self.__set_guild_attributes(Guild(), data)
                session.add(new_guild)
                session.commit()

                # Удаление записей старше месяца
            month_old_date = datetime.now() - timedelta(days=30)
            session.query(Guild).filter(Guild.last_db_update_time < month_old_date).delete()
            session.commit()
        except Exception as e:
            raise DatabaseBuildError(f"An error occurred while building the Guild database: {e}") from e