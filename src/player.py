# src/player.py
import io
import json
import os
from collections import defaultdict
from typing import List

import aiohttp
import pytz
import requests
from dateutil.relativedelta import relativedelta

from datetime import datetime, timedelta, time
import plotly.graph_objects as go
import plotly.io as pio

from create_bot import bot
from db_models import Player, Guild
from pytz import timezone
from dotenv import load_dotenv

from settings import async_session_maker
from src.errors import Status404Error, AddIdsError, DatabaseBuildError
from src.utils import get_new_day_start, format_scores, get_localized_datetime, get_end_date
from sqlalchemy import select, delete, func, text

load_dotenv()

# utc_tz = timezone('UTC')
#
# tz = str(os.environ.get("TIME_ZONE"))
# time_tz = timezone(tz)

API_LINK = f"{os.environ.get('API_HOST')}:{os.environ.get('API_PORT')}"
GUILD_POST_DATA = {
    "payload": {
        "guildId": os.environ.get("GUILD_ID"),
        "includeRecentGuildActivityInfo": True
    },
    "enums": False
}


class PlayerData:
    @staticmethod
    async def get_swgoh_player_data(ally_code):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://api.swgoh.gg/player/{str(ally_code)}/') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']

    async def __add_ids(self):
        try:
            with open("./ids.json", encoding="utf-8") as f:
                data = json.load(f)  # Загрузить список словарей

            result = {}  # Создать пустой словарь

            for d in data:  # Пройтись по всем словарям в списке
                for key, value in d.items():  # Пройтись по всем парам ключ-значение в словаре
                    result[key] = value  # Добавить ключ и значение в результат
            return result
        except Exception as e:
            raise AddIdsError(f"An error occurred while getting ids.json data: {e}") from e

    async def create_or_update_player_data(self, data: dict):
        new_day_start = get_new_day_start()
        async with async_session_maker() as session:
            existing_user_today = await session.execute(
                select(Player).filter_by(ally_code=data['ally_code']).filter(
                    Player.update_time >= new_day_start))
            existing_user_today = existing_user_today.scalars().first()

            if existing_user_today:
                print(f"{data['name']}: old")
                await self.__set_player_attributes(existing_user_today, data)

                await session.commit()
            else:
                print(f"{data['name']}: new")
                new_user = await self.__set_player_attributes(Player(), data)
                session.add(new_user)
                await session.commit()

            month_old_date = datetime.now() - timedelta(days=30)
            await session.execute(delete(Player).where(Player.update_time < month_old_date))
            await session.commit()

    async def __set_player_attributes(self, player: Player, data):
        """Устанавливает значения из переданного словаря в модель Player"""
        player.name = data['name']
        player.ally_code = data['ally_code']
        player.tg_id = data['existing_player']['tg_id']
        player.tg_nic = data['existing_player']['tg_nic']
        player.update_time = datetime.now()
        player.reid_points = data['reid_points']

        player.lastActivityTime = get_localized_datetime(int(data['lastActivityTime']),
                                                         str(os.environ.get('TIME_ZONE')))

        player.level = data['level']
        player.player_id = data['playerId']
        player.arena_rank = data['comlink_arena_rank']
        player.fleet_arena_rank = data['comlink_fleet_arena_rank']
        player.galactic_power = data['comlink_galactic_power']
        player.character_galactic_power = data['character_galactic_power']
        player.ship_galactic_power = data['ship_galactic_power']
        player.guild_join_time = datetime.strptime(data['guild_join_time'], "%Y-%m-%dT%H:%M:%S")
        player.url = 'https://swgoh.gg' + data['url']

        last_updated_utc = datetime.strptime(data['last_updated'], '%Y-%m-%dT%H:%M:%S')
        player.last_swgoh_updated = last_updated_utc
        player.guild_currency_earned = data['guild_points']
        player.arena_leader_base_id = data['arena_leader_base_id']
        player.ship_battles_won = data['ship_battles_won']
        player.pvp_battles_won = data['pvp_battles_won']
        player.pve_battles_won = data['pve_battles_won']
        player.pve_hard_won = data['pve_hard_won']
        player.galactic_war_won = data['galactic_war_won']
        player.guild_raid_won = data['guild_raid_won']
        player.guild_exchange_donations = data['guild_exchange_donations']
        player.season_status = data['season_status']
        player.season_full_clears = data['season_full_clears']
        player.season_successful_defends = data['season_successful_defends']
        player.season_league_score = data['season_league_score']
        player.season_undersized_squad_wins = data['season_undersized_squad_wins']
        player.season_promotions_earned = data['season_promotions_earned']
        player.season_banners_earned = data['season_banners_earned']
        player.season_offensive_battles_won = data['season_offensive_battles_won']
        player.season_territories_defeated = data['season_territories_defeated']

        return player

    async def update_players_data(self):
        """Вытаскивает данные о гильдии и участниках, а после
         по имени участника гоняет циклом обновление бд для каждого участника"""
        # try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.swgoh.gg/guild-profile/{os.environ.get('GUILD_ID')}") as swgoh_request:
                swgoh_request.raise_for_status()
                data = await swgoh_request.json()

        error_list = []
        existing_players = await self.__add_ids()

        # try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_LINK}/guild", json=GUILD_POST_DATA) as comlink_request:
                comlink_request.raise_for_status()
                raw_data = await comlink_request.json()

        guild_data_dict = {player['playerName']: player for player in raw_data['guild']['member']}
        galactic_power_dict = {player: int(data['galacticPower']) for player, data in guild_data_dict.items()}
        for i in data['data']['members']:
            if str(i['ally_code']) in existing_players:
                final_data: dict = await self.get_swgoh_player_data(i['ally_code'])
                final_data.update({'guild_join_time': i['guild_join_time']})
                final_data.update({'existing_player': existing_players[str(i['ally_code'])]})
                # try:
                post_data = {
                    "payload": {
                        "allyCode": f"{i['ally_code']}"
                    },
                    "enums": False
                }
                comlink_player_request = requests.post(f"{API_LINK}/player", json=post_data)
                comlink_player_request.raise_for_status()
                comlink_data = comlink_player_request.json()
                final_data.update({'name': comlink_data['name']})
                final_data.update({'level': comlink_data['level']})
                final_data.update({'playerId': comlink_data['playerId']})
                final_data.update({'lastActivityTime': comlink_data['lastActivityTime']})
                final_data.update({'comlink_arena_rank': comlink_data['pvpProfile'][0]['rank']})
                final_data.update({'comlink_fleet_arena_rank': comlink_data['pvpProfile'][1]['rank']})
                final_data.update({'comlink_galactic_power': galactic_power_dict[comlink_data['name']]})
                try:
                    member_contribution_dict = {item['type']: item['currentValue'] for item in
                                                guild_data_dict[comlink_data['name']]['memberContribution']}
                    final_data.update({'season_status': len(guild_data_dict[comlink_data['name']]['seasonStatus'])})

                    final_data.update({'reid_points': member_contribution_dict[2]})
                    final_data.update({'guild_points': member_contribution_dict[1]})
                except KeyError:
                    message = f"Игрок {i['player_name']} удален из гильдии. Обновите ids.json. Сотрите малейшие воспоминания об этом непотребстве!"
                    error_list.append(message)
                    await bot.send_message(int(os.environ.get('OFFICER_CHAT_ID')), message)
                    continue
                await self.create_or_update_player_data(final_data)

            else:
                message = f"Игрок {i['player_name']} отсутствует в гильдии. Обновите ids.json и дождитесь обновления swgoh.gg"
                error_list.append(message)

        print("\n".join(error_list))
        print("Данные игроков в базе обновлены.")

    async def extract_data(self, player: Player):
        """Выводит все данные по игроку в виде строки"""
        data_dict = player.__dict__
        formatted_string = "\n".join(
            f"{key}: {value}\n{'-' * 30}" for key, value in data_dict.items() if
            not key.startswith('_') and key not in ('id', 'tg_id'))
        return formatted_string


class PlayerScoreService:
    @staticmethod
    async def get_recent_players():
        """Создает список из всех записей о согильдийцах за текущие игровые сутки"""
        new_day_start = get_new_day_start()
        async with async_session_maker() as session:  # открываем асинхронную сессию
            query = await session.execute(
                select(Player).filter(
                    Player.update_time >= new_day_start))
            result = query.scalars().all()
            return result

    @staticmethod
    async def get_all_players():
        """Список всех записей по игрокам за все время"""
        async with async_session_maker() as session:  # открываем асинхронную сессию
            query = await session.execute(select(Player))  # выполняем асинхронный запрос
            return query.scalars().all()

    @staticmethod
    def get_sorted_scores(players):

        # Создаем словарь, где будем суммировать очки
        player_scores = defaultdict(int)

        # Это переменная для подсчета общего количества очков
        total_points = 0

        # Проходим по всем записям и суммируем очки
        for player in players:
            # Проверяем, является ли reid_points строкой и преобразовываем ее в int, если это так
            reid_points = int(player.reid_points) if isinstance(player.reid_points, str) else player.reid_points

            player_scores[player.name] += reid_points
            total_points += reid_points

        return sorted(player_scores.items(), key=lambda x: x[1], reverse=True), total_points

    @staticmethod
    async def get_raid_scores():
        recent_players = await PlayerScoreService.get_recent_players()
        if not recent_players:
            return "Нет данных об игроках."
        sorted_scores, _ = PlayerScoreService.get_sorted_scores(recent_players)
        scores = await format_scores(sorted_scores, filter_points=None)
        scores.insert(0,
                      f"\nСписок купонов за день\nОбновление дня в"
                      f" {os.environ.get('DAY_UPDATE_HOUR')}:{os.environ.get('DAY_UPDATE_MINUTES')}"
                      f" по {os.environ.get('TZ_SUFFIX')}\n")
        return f"\n{'-' * 30}\n".join(scores)

    @staticmethod
    async def get_raid_scores_all():
        """Возвращает строку из списка всх рейд купонов по народу за месяц"""
        all_players = await PlayerScoreService.get_all_players()
        if not all_players:
            return "Нет данных об игроках."
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        end_date = await get_end_date()
        async with async_session_maker() as session:  # открываем асинхронную сессию
            query = await session.execute(
                select(Player).filter(
                    Player.update_time >= start_date,
                    Player.update_time <= end_date
                ).order_by(Player.update_time).limit(1)
            )
            player: Player = query.scalar_one()

        sorted_scores, total_points = PlayerScoreService.get_sorted_scores(all_players)
        scores = await format_scores(sorted_scores, filter_points=None, total=False)
        scores.append(f"Всего купонов от {player.update_time.strftime('%d.%m.%y')}:    {total_points}")

        today = datetime.today().date()
        if today == end_date.date():
            scores.insert(0,
                           f"⚠️⚠️⚠️ВНИМАНИЕ!!!⚠️⚠️⚠️\n🖊Последний день месяца! Эту таблицу надо сохранить🖊\nДанные за {end_date}\n")
        else:
            scores.insert(0, f"\n🗡Список всех купонов за текущий месяц:🗡\n")

        return f"\n{'-' * 30}\n".join(scores)

    @staticmethod
    async def get_reid_lazy_fools():
        """Возвращает строку из списка всех кто еще не сдал 600 энки на текущий момент"""
        recent_players = await PlayerScoreService.get_recent_players()
        if not recent_players:
            return "Нет данных об игроках."
        sorted_scores, _ = PlayerScoreService.get_sorted_scores(recent_players)
        scores = await format_scores(sorted_scores, filter_points=600)
        # получение текущей временной зоны
        tz_name = os.environ.get('TIME_ZONE')
        t_zone = pytz.timezone(tz_name)

        # конвертация времени
        local_time = recent_players[0].update_time.astimezone(t_zone)

        # форматирование времени в минуты
        local_time_str = local_time.strftime('%H:%M')

        scores.insert(0, f"\nСписок не сдавших 600 энки на {local_time_str} по {os.environ.get('TZ_SUFFIX')}\n")
        return f"\n{'-' * 30}\n".join(scores)





class PlayerPowerService:
    @staticmethod
    async def get_galactic_power_all():
        """Возвращает строку из списка всей галактической мощи игроков за месяц"""
        all_players = await PlayerScoreService.get_all_players()
        if not all_players:
            return "Нет данных об игроках."
        now = get_new_day_start()
        start_date = datetime(now.year, now.month, 1)
        end_date = await get_end_date()

        # Get the players for the start of the month
        start_month_players = await PlayerPowerService.get_players_for_first_available_date_in_month(start_date)
        # Get the players for the current date
        current_players = await PlayerPowerService.get_players_for_date(now)
        start_month_powers = PlayerPowerService.get_powers(start_month_players)
        current_powers = PlayerPowerService.get_powers(current_players)
        power_diffs, total_diff = PlayerPowerService.get_power_diffs(start_month_powers, current_powers)

        powers = await format_scores(power_diffs, filter_points=None, total=False, powers=True)
        powers.append(
            f"Общая разница в галактической мощи\nот {start_date.strftime('%d.%m.%y')} до {now.strftime('%d.%m.%y')}:    {total_diff}")

        today = datetime.today().date()
        if today == end_date.date():
            powers.insert(0,
                          f"⚠️⚠️⚠️ВНИМАНИЕ!!!⚠️⚠️⚠️\n🖊🖊Последний день месяца! Эту таблицу надо сохранить🖊🖊\nДанные за {end_date}\n")
        else:
            powers.insert(0, f"\n⚔️Список изменения галактической мощи за месяц:⚔️\n")

        return f"\n{'-' * 30}\n".join(powers)

    @staticmethod
    async def get_players_for_date(date):
        """Get all player data for a specific date"""
        start_date_time = datetime.combine(date, time(16, 30))
        end_date_time = datetime.combine(date + timedelta(days=1), time(16, 30))
        async with async_session_maker() as session:  # открываем асинхронную сессию
            query = await session.execute(
                select(Player).filter(
                    Player.update_time >= start_date_time,
                    Player.update_time < end_date_time
                )
            )
        return query.scalars().all()

    @staticmethod
    async def get_players_for_first_available_date_in_month(date):
        """Get all player data for the first available date in the month"""
        start_date_time = datetime.combine(date, time(16, 30))
        end_date_time = datetime.combine(datetime.now(), time(16, 30))
        async with async_session_maker() as session:  # открываем асинхронную сессию
            query = await session.execute(
                select(Player).filter(
                    Player.update_time >= start_date_time,
                    Player.update_time < end_date_time
                ).order_by(Player.update_time)
            )
        return query.scalars().all()

    @staticmethod
    def get_powers(players):
        # Создаем словарь, где будем сохранять мощь
        player_powers = {}

        # Проходим по всем записям и сохраняем силу
        for player in players:
            # Проверяем, является ли galactic_power строкой и преобразовываем ее в int, если это так
            galactic_power = int(player.galactic_power) if isinstance(player.galactic_power,
                                                                      str) else player.galactic_power

            player_powers[player.name] = galactic_power

        return player_powers

    @staticmethod
    def get_power_diffs(start_month_powers, current_powers):
        # Создаем словарь, где будем суммировать разницу в мощи
        power_diffs = {}

        # Это переменная для подсчета общей разницы в галактической силе
        total_diff = 0

        # Проходим по всем записям и считаем разницу в мощи
        for player_name, start_month_power in start_month_powers.items():
            if player_name not in current_powers:
                continue
            current_power = current_powers[player_name]
            diff = current_power - start_month_power

            power_diffs[player_name] = diff
            total_diff += diff

        return sorted(power_diffs.items(), key=lambda x: x[1], reverse=True), total_diff



