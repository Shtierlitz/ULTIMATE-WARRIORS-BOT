# api_utils.py
import json
import os

import requests
from sqlalchemy import func

from create_bot import session
from datetime import datetime, timedelta, time

from db_models import Player, Guild
from pytz import timezone
from dotenv import load_dotenv
from swgoh_comlink import SwgohComlink

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


class Status404Error(Exception):
    pass


class DatabaseBuildError(Exception):
    """Raised when there is an error building the database"""
    pass


class AddIdsError(Exception):
    """Raised when there is an error building the database"""
    pass


class PlayerData:
    @staticmethod
    def player_data_by_code(ally_code):
        player_request = requests.get(f'http://api.swgoh.gg/player/{ally_code}/')
        if player_request.status_code == 200:
            data = player_request.json()
            return data['data']

    def __add_ids(self):
        try:
            with open("./api/ids.json", encoding="utf-8") as f:
                data = json.load(f)  # Загрузить список словарей

            result = {}  # Создать пустой словарь

            for d in data:  # Пройтись по всем словарям в списке
                for key, value in d.items():  # Пройтись по всем парам ключ-значение в словаре
                    result[key] = value  # Добавить ключ и значение в результат
            return result
        except Exception as e:
            raise AddIdsError(f"An error occurred while getting ids.json data: {e}") from e

    def create_or_update_player_data(self, data: dict):
        """Создает или обновляет данные пользователя на текущий день"""
        try:
            new_day_start = get_new_day_start()

            existing_user_today = session.query(Player).filter_by(name=data['name']).filter(
                Player.update_time >= new_day_start).first()

            # Если пользователь уже существует
            if existing_user_today:
                print('existing_user_today')
                self.__set_player_attributes(existing_user_today, data)
                session.commit()
            else:
                print('existing_user_older')
                # Добавляем нового пользователя
                new_user = self.__set_player_attributes(Player(), data)
                session.add(new_user)
                session.commit()

                # Удаление записей старше месяца
            month_old_date = datetime.now() - timedelta(days=30)
            session.query(Player).filter(Player.update_time < month_old_date).delete()
            session.commit()
        except Exception as e:
            raise DatabaseBuildError(f"An error occurred while building the Player database: {e}") from e

    def __set_player_attributes(self, player, data):
        timestamp_ms = data['lastActivityTime']
        timestamp = int(timestamp_ms) / 1000

        player.name = data['name']

        guild_join_time_utc = datetime.strptime(data['guild_join_time'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=utc_tz)
        player.guild_join_time = guild_join_time_utc.astimezone(time_tz)

        last_activity_time_utc = datetime.fromtimestamp(timestamp).replace(tzinfo=utc_tz)
        player.lastActivityTime = last_activity_time_utc.astimezone(time_tz)

        player.reid_points = int(data['reid_points'])
        player.guild_points = int(data['guild_points'])
        player.player_id = data['existing_player']['tg_id']
        player.update_time = datetime.now(time_tz)
        player.ally_code = data['ally_code']
        player.arena_leader_base_id = data['arena_leader_base_id']
        player.arena_rank = data['arena_rank']
        player.level = data['level']

        last_updated_utc = datetime.strptime(data['last_updated'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=utc_tz)
        player.last_updated = last_updated_utc.astimezone(time_tz)

        player.galactic_power = data['galactic_power']
        player.character_galactic_power = data['character_galactic_power']
        player.ship_galactic_power = data['ship_galactic_power']
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
        player.url = 'https://swgoh.gg' + data['url']

        return player

    def update_players_data(self):
        """Вытаскивает данные о гильдии и участниках, а после
         по имени участника гоняет циклом обновление бд для каждого участника"""
        try:
            swgoh_request = requests.get(f"http://api.swgoh.gg/guild-profile/{os.environ.get('GUILD_ID')}")
            error_list = []
            swgoh_request.raise_for_status()
            data = swgoh_request.json()
            existing_players = self.__add_ids()

            try:
                comlink_request = requests.post(f"{API_LINK}/guild", json=GUILD_POST_DATA)
                comlink_request.raise_for_status()
                raw_data = comlink_request.json()
                guild_data_dict = {player['playerName']: player for player in raw_data['guild']['member']}
            except requests.exceptions.HTTPError:
                raise Status404Error(f"Комлинк с гильдией не отвечает при построении базы для игрока")

            for i in data['data']['members']:
                if str(i['ally_code']) in existing_players:
                    data: dict = self.player_data_by_code(i['ally_code'])
                    data.update({'guild_join_time': i['guild_join_time']})
                    data.update({'existing_player': existing_players[str(i['ally_code'])]})

                    post_data = {
                        "payload": {
                            "allyCode": f"{i['ally_code']}"
                        },
                        "enums": False
                    }
                    comlink_player_request = requests.post(f"{API_LINK}/player", json=post_data)

                    try:
                        comlink_player_request.raise_for_status()
                        post_data = comlink_player_request.json()
                        data.update({'name': post_data['name']})
                        data.update({'level': post_data['level']})
                        data.update({'playerId': post_data['playerId']})
                        data.update({'lastActivityTime': post_data['lastActivityTime']})
                        member_contribution_dict = {item['type']: item['currentValue'] for item in
                                                    guild_data_dict[post_data['name']]['memberContribution']}
                        data.update({'reid_points': member_contribution_dict[2]})
                        data.update({'guild_points': member_contribution_dict[1]})
                        data.update({'season_status': len(guild_data_dict[post_data['name']]['seasonStatus'])})

                        self.create_or_update_player_data(data)

                    except Exception as e:
                        raise Status404Error(
                            f"Комлинк с гильдией не отвечает при построении базы для игрока {e}") from e

                else:
                    error_list.append(f"Игрок {i['player_name']} отсутствует в гильдии. Обновите ids.json")

            print("\n".join(error_list))
            print("Данные игроков в базе обновлены.")

        except Exception as e:
            raise Status404Error(f"An error occurred while building the Player database: {e}") from e

    def extract_data(self, player: Player):
        """Выводит все данные по игроку"""
        data_dict = player.__dict__
        formatted_string = "\n".join(
            f"{key}: {value}\n{'-' * 30}" for key, value in data_dict.items() if not key.startswith('_'))
        return formatted_string

    @staticmethod
    def get_player_filtered_data(data: Player, key: str):
        """Возвращает данные игрока по ключу"""
        return data.__dict__[key]

    @staticmethod
    def get_raid_scores():
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # получить данные за (сегодня)
        recent_players = session.query(Player).filter(
            func.date(Player.update_time).in_([today])
        ).all()

        if not recent_players:
            return "Нет данных об игроках."

        # отбираем самую свежую запись для каждого игрока
        players_dict = {}
        for player in recent_players:
            if player.name not in players_dict or player.update_time > players_dict[player.name].update_time:
                players_dict[player.name] = player

        # форматируем результат в нужный вид и сортируем по убыванию очков
        raid_scores = [
            f"{player.name} {player.reid_points} купонов"
            for player in sorted(players_dict.values(), key=lambda x: x.reid_points, reverse=True)
        ]

        return f"\n{'-' * 30}\n".join(raid_scores)

    @staticmethod
    def get_reid_lazy_fools():
        today = datetime.now().date()

        # получить данные за (сегодня)
        recent_players = session.query(Player).filter(
            func.date(Player.update_time).in_([today])
        ).all()

        if not recent_players:
            return "Нет данных об игроках."

        # отбираем самую свежую запись для каждого игрока
        players_dict = {}
        for player in recent_players:
            if player.name not in players_dict or player.update_time > players_dict[player.name].update_time:
                players_dict[player.name] = player

        # форматируем результат в нужный вид и сортируем по убыванию очков
        reid_scores = [
            f"{player.name} {player.reid_points} купонов"
            for player in sorted(players_dict.values(), key=lambda x: x.reid_points, reverse=True)
            if player.reid_points < 600  # добавляем условие
        ]

        # добавляем время обновления, используя время обновления первого игрока в списке
        update_time = recent_players[0].update_time.strftime('%H:%M:%S')
        reid_scores.insert(0,
                           f"Список не сдавших 600 купонов по состоянию на {update_time} {os.environ.get('TZ_SUFIX')}:\n")

        return f"\n{'-' * 30}\n".join(reid_scores)


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


# Может еще пригодится. Пока оставлю.
# class GameData:
#
#     def __get_game_version(self) -> str:
#         """Возвращает строку с последней версией игры"""
#         try:
#             comlink_request = requests.post(f"{API_LINK}/metadata")
#             comlink_request.raise_for_status()
#             data = comlink_request.json()
#             return data['latestGamedataVersion']
#         except requests.exceptions.HTTPError:
#             raise Status404Error("There was an error getting comlink metadata.")
#
#     def get_game_data(self) -> dict:
#         """Формирует словарь с данными из игры (только нужные)"""
#         version: str = self.__get_game_version()
#         post_data = {
#             "payload": {
#                 "version": version,
#                 "includePveUnits": True,
#                 "requestSegment": 2
#             },
#             "enums": False
#         }
#         result = {}
#         try:
#             comlink_request = requests.post(f"{API_LINK}/data", json=post_data)
#             comlink_request.raise_for_status()
#             data = comlink_request.json()
#             print(data.keys())
#             for i in data['statModSet']:
#                 print(i)
#         except requests.exceptions.HTTPError:
#             raise Status404Error("There was an error getting comlink metadata.")
#         return result


def gac_statistic() -> tuple:
    """Выдает статистику по игрокам зарегались на ВГ или нет."""
    current_date = datetime.now().date()
    players_list = session.query(Player).filter(func.date(Player.update_time) == current_date)
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
    """Возвращает начало нового дня в 16:30."""
    now = datetime.now()
    today = now.date()
    new_day_start = datetime.combine(today, time(16, 30))

    if now < new_day_start:
        new_day_start = new_day_start - timedelta(days=1)

    return new_day_start


def get_event_data():
    # post_data = {
    #     "enums": True
    # }
    # result = {}
    # try:
    #     comlink_request = requests.post(f"{API_LINK}/getEvents", json=post_data)
    #     comlink_request.raise_for_status()
    #     data = comlink_request.json()
    #
    #     for i in data['gameEvent']:
    #         for j in i['instance']:
    #             print(j['displayStartTime'])
    #             timestamp_ms = j['displayStartTime']
    #             timestamp = int(timestamp_ms) / 1000
    #             time = datetime.fromtimestamp(timestamp).replace(tzinfo=utc_tz)
    #             # Если год не текущий, переходим к следующей итерации
    #             # if time.year != datetime.now().year:
    #             #     continue
    #             print(i['id'], time.date())
    #
    #
    # except requests.exceptions.HTTPError:
    #     raise Status404Error("There was an error getting comlink metadata.")
    # return result
    comlink = SwgohComlink(url='http://localhost:3200', stats_url='http://localhost:3223')
    player_data = comlink.get_player(796483269)
    player_roster = player_data['rosterUnit']
    roster_with_stats = comlink.get_unit_stats(player_roster)
    guild_id = player_data['guildId']
    guild = comlink.get_guild(guild_id)
    guild_name = guild['profile']['name']
    print(guild)

    # docker network create swgoh
    # docker run --name swgoh-comlink --network swgoh -d --restart always --env APP_NAME=shtierlitz_comlinc -p 3200:3000 ghcr.io/swgoh-utils/swgoh-comlink:latest
    # docker build -t swgoh-stats .
    # docker run --rm -it -p 3223:3223 --env-file .env swgoh-stats - хз не знаю
    # docker run --name=swgoh-stats --network swgoh -d --restart always --env-file .env-swgoh-stats -p 3223:3223 -v $(pwd)/statCalcData:/app/statCalcData ghcr.io/swgoh-utils/swgoh-stats:latest