# src/player.py

import json
import os
from collections import defaultdict
from typing import List

import aiohttp
import pytz
import requests

from datetime import datetime, timedelta, time

from create_bot import bot
from db_models import Player

from settings import async_session_maker
from src.errors import AddIdsError
from src.utils import get_new_day_start, format_scores, get_localized_datetime, get_end_date
from sqlalchemy import select, delete, func


HOURS, MINUTES = int(os.environ.get('DAY_UPDATE_HOUR', 16)), int(os.environ.get('DAY_UPDATE_MINUTES', 30))

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
                await self._set_player_attributes(existing_user_today, data)

                await session.commit()
            else:
                print(f"{data['name']}: new")
                new_user = await self._set_player_attributes(Player(), data)
                session.add(new_user)
                await session.commit()

            month_old_date = datetime.now() - timedelta(days=30)
            await session.execute(delete(Player).where(Player.update_time < month_old_date))
            await session.commit()

    async def _set_player_attributes(self, player: Player, data):
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
        try:
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
        except Exception as e:
            message = f"❌❌Произошла ошибка при парсинге API в классе Player❌❌\n\n{e}"
            await bot.send_message(int(os.environ.get('MY_ID')), message)

        print("\n".join(error_list))
        print("Данные игроков в базе обновлены.")

    async def extract_data(self, player: Player):
        """Выводит все данные по игроку в виде строки"""
        data_dict = player.__dict__
        # для отладки
        # for key, value in data_dict.items():
        #     print(key, value)
        output_structure = [
            {"description": "Имя аккаунта", "value": data_dict['name']},
            {"description": "Код союзника", "value": data_dict['ally_code']},
            {"description": "Последняя активность", "value": data_dict['lastActivityTime']},
            {"description": "Уровень", "value": data_dict['level']},
            {"description": "Ссылка на swgoh", "value": data_dict['url']},
            {"description": "Ник в телеграме", "value": f"@{data_dict['tg_nic']}"},
            {"description": "Галактическая мощь", "value": data_dict['galactic_power']},
            {"description": "Сданых купонов за день", "value": data_dict['reid_points']},
            {"description": "Ранг на пешей арене", "value": data_dict['arena_rank']},
            {"description": "Ранг на арене флота", "value": data_dict['fleet_arena_rank']},
            {"description": "Всего пожертвованных деталей", "value": data_dict['guild_exchange_donations']},
            {"description": "Галактическая мощь пешки (swgoh)", "value": data_dict['character_galactic_power']},
            {"description": "Галактическая мощь флота (swgoh)", "value": data_dict['ship_galactic_power']},
            {"description": "PVP побед", "value": data_dict['pvp_battles_won']},
            {"description": "PVE побед простых", "value": data_dict['pve_battles_won']},
            {"description": "PVE побед сложных", "value": data_dict['pve_hard_won']},
            {"description": "Побед на Галактических Войнах", "value": data_dict['galactic_war_won']},
            {"description": "Статус сезона", "value": data_dict['season_status']},
            {"description": "Зачищенных територий в сезоне", "value": data_dict['season_territories_defeated']},
            {"description": "Полных зачисток в сезоне", "value": data_dict['season_full_clears']},
            {"description": "Успешных оборонительных битв в сезоне", "value": data_dict['season_successful_defends']},
            {"description": "Успешных атак в сезоне", "value": data_dict['season_offensive_battles_won']},
            {"description": "Очков лиги в сезоне", "value": data_dict['season_league_score']},
            {"description": "Повышений в сезоне", "value": data_dict['season_promotions_earned']},
            {"description": "Ссылка на swgoh", "value": data_dict['url']},
            {"description": "Последнее обновление базы",
             "value": data_dict['update_time'].strftime('%d.%m.%y : %H.%M')},
            {"description": "Последнее обновление на swgoh",
             "value": data_dict['last_swgoh_updated'].strftime('%d.%m.%y : %H.%M')}
        ]

        new_string = "👀Полные данные об игроке👀\n\n"
        for item in output_structure:
            new_string += f"{item['description']}: {item['value']}\n{'-' * 30}\n"

        return new_string


class PlayerScoreService:
    @staticmethod
    async def get_recent_players(period: str = None) -> List[Player]:
        """Создает список из всех записей о согильдийцах за текущие игровые сутки"""
        new_day_start = get_new_day_start()
        if period == "yesterday":
            start_time = new_day_start - timedelta(days=1)
            end_time = new_day_start
        elif period == "week":
            start_time = new_day_start - timedelta(days=7)
            end_time = new_day_start
        elif period == "month":
            start_time = new_day_start - timedelta(days=30)
        else:
            # Устанавливаем начальное время для "сегодняшнего" дня и конечное время как "сейчас"
            start_time = new_day_start
            end_time = datetime.now()

        async with async_session_maker() as session:  # открываем асинхронную сессию
            query = await session.execute(
                select(Player).filter(
                    Player.update_time >= start_time, Player.update_time < end_time))
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
                      f" {HOURS}:{MINUTES}"
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
    async def get_reid_lazy_fools(period: str = None):
        """Возвращает строку из списка всех кто еще не сдал 600 энки на текущий момент"""
        if period == 'yesterday':
            recent_players = await PlayerScoreService.get_recent_players(period)
        elif period == 'week':
            recent_players = await PlayerScoreService.get_recent_players(period)
        elif period == 'month':
            recent_players = await PlayerScoreService.get_recent_players(period)
        else:
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

    @staticmethod
    async def get_least_reid_point_players(period: str = "week", least: bool = True):
        """Return players with the lowest or highest total reid points in a week or month."""

        # Determine time frame
        days_ago = 7 if period == "week" else 30 if period == "month" else None
        if days_ago is None:
            return "Invalid period. Must be either 'week' or 'month'."

        # Define the start time
        start_time = datetime.now() - timedelta(days=days_ago)

        # Fetch players and their total reid points for the specified period
        async with async_session_maker() as session:
            result = await session.execute(
                select(Player)
                .filter(Player.update_time >= start_time)
            )
        recent_players = result.scalars().all()

        # Calculate total reid points for each player
        player_scores = {}
        for player in recent_players:
            if player.name in player_scores:
                player_scores[player.name] += int(player.reid_points)
            else:
                player_scores[player.name] = int(player.reid_points)

        # Sort players by total reid points
        sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=not least)

        return sorted_players

    @staticmethod
    async def get_least_reid_lazy_fools(period: str = "week", least: bool = True):
        """Return a string with the list of players who have the least or most total reid points."""

        # Get the sorted list of players with their total reid points
        sorted_players = await PlayerScoreService.get_least_reid_point_players(period=period, least=least)

        if not sorted_players:
            return "No player data."

        if period == 'week':
            points = 4200
            per = "неделю"
        else:
            points = 18000
            per = "месяц"

        # Filter players who have less than the expected points and limit to 10
        if least:
            sorted_players = [player for player in sorted_players if player[1] < points][:10]
            scores = [f"{index + 1}. {name}: {player_points}" for index, (name, player_points) in
                      enumerate(sorted_players)][::-1]
        else:
            sorted_players = sorted_players[:10]
            scores = [f"{index + 1}. {name}: {player_points}" for index, (name, player_points) in
                      enumerate(sorted_players)]

        scores.insert(0,
                      f"\n{'Список отстающих по энке' if least else 'Список лидеров по энке'} за {per}.\n\nДолжно быть по {points}\n")

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

        # для тестирования
        # start_month_players_sorted = sorted(start_month_players, key=lambda player: player.galactic_power)
        # print([[i.name, i.galactic_power] for i in start_month_players_sorted])
        # current_players_sorted = sorted(current_players, key=lambda player: player.galactic_power)  # Сортировка по galactic_power
        # print([[i.name, i.galactic_power] for i in current_players_sorted])

        start_month_powers = PlayerPowerService.get_powers(start_month_players)
        current_powers = PlayerPowerService.get_powers(current_players)
        power_diffs, total_diff = PlayerPowerService.get_power_diffs(start_month_powers, current_powers)

        powers = await format_scores(power_diffs, filter_points=None, total=False, powers=True)

        if now.time() < time(HOURS, MINUTES):
            now -= timedelta(days=1)
        powers.append(
            f"Общая разница в галактической мощи\nот {(start_month_players[0].update_time - timedelta(days=1)).strftime('%d.%m.%y')} до {now.strftime('%d.%m.%y')}:    {total_diff}")

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
        start_date_time = datetime.combine(date, time(HOURS, MINUTES))
        end_date_time = datetime.combine(date + timedelta(days=1), time(HOURS, MINUTES))
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
        async with async_session_maker() as session:  # открываем асинхронную сессию
            first_date_of_month = date.replace(day=1)
            first_date_time = datetime.combine(first_date_of_month, time(HOURS, MINUTES))

            # Check if there are any records for the first day of the month
            result = await session.execute(
                select(func.count()).where(
                    func.DATE(Player.update_time) == func.DATE(first_date_time)
                )
            )
            count = result.scalar_one()

            if count > 0:
                # If there are records for the first day of the month, use them
                query = await session.execute(
                    select(Player).where(
                        func.DATE(Player.update_time) == func.DATE(first_date_time)
                    )
                )
            else:
                # If there are no records for the first day of the month, use the minimum date
                result = await session.execute(
                    select(func.min(Player.update_time))
                )
                min_date = result.scalar_one()
                query = await session.execute(
                    select(Player).where(
                        func.DATE(Player.update_time) == func.DATE(min_date)
                    )
                )
            players = query.scalars().all()
        return players

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
