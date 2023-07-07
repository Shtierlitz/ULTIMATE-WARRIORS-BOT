# api_utils.py
import json
import os

import requests
from sqlalchemy import func

from create_bot import session
from datetime import datetime, timedelta

from db_models import Player, Guild
from pytz import timezone
from dotenv import load_dotenv

load_dotenv()

utc_tz = timezone('UTC')

tz = str(os.environ.get("TIME_ZONE"))
time_tz = timezone(tz)

API_LINK = f"{os.environ.get('API_HOST')}:{os.environ.get('API_PORT')}"


class PlayerData:
    @staticmethod
    def player_data_by_code(ally_code):
        player_request = requests.get(f'http://api.swgoh.gg/player/{ally_code}/')
        if player_request.status_code == 200:
            data = player_request.json()
            return data['data']

    def __add_ids(self):
        with open("./api/ids.json", encoding="utf-8") as f:
            data = json.load(f)  # Загрузить список словарей

        result = {}  # Создать пустой словарь

        for d in data:  # Пройтись по всем словарям в списке
            for key, value in d.items():  # Пройтись по всем парам ключ-значение в словаре
                result[key] = value  # Добавить ключ и значение в результат
        return result

    def create_or_update_player_data(self, data: dict):
        """Создает или обновляет данные пользователя на текущий день"""
        # Проверка наличия пользователя в базе данных

        existing_user_today = session.query(Player).filter_by(name=data['name']).filter(
            func.date(Player.update_time) == datetime.today().date()).first()
        existing_user_older = session.query(Player).filter_by(name=data['name']).filter(
            func.date(Player.update_time) < datetime.today().date()).first()

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
        try:
            player.player_id = data['existing_player']['tg_id']
        except Exception as e:
            print(f"Ошибка: {e}")
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

        guild_request = requests.get(f"http://api.swgoh.gg/guild-profile/{os.environ.get('GUILD_ID')}")
        if guild_request.status_code == 200:
            data = guild_request.json()
            # print(data['data']['members'])
            existing_players = self.__add_ids()
            error_list = []
            guild_post_data = {
                "payload": {
                    "guildId": os.environ.get("GUILD_ID"),
                    "includeRecentGuildActivityInfo": True
                },
                "enums": False
            }
            guild_data_dict = {}
            comlink_guild_data = requests.post(f"{API_LINK}/guild", json=guild_post_data)
            if comlink_guild_data.status_code == 200:
                raw_data = comlink_guild_data.json()
                guild_data_dict = {player['playerName']: player for player in raw_data['guild']['member']}

            else:
                error_list.append(f"Комлинк с гильдией не отвечает: {comlink_guild_data.status_code}")
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

                    if comlink_player_request.status_code == 200:
                        post_data = comlink_player_request.json()
                        data.update({'name': post_data['name']})
                        data.update({'level': post_data['level']})
                        data.update({'playerId': post_data['playerId']})
                        data.update({'lastActivityTime': post_data['lastActivityTime']})
                        member_contribution_dict = {item['type']: item['currentValue'] for item in
                                                    guild_data_dict[post_data['name']]['memberContribution']}
                        print(member_contribution_dict[1], member_contribution_dict[2])

                        data.update({'reid_points': member_contribution_dict[2]})
                        data.update({'guild_points': member_contribution_dict[1]})
                        data.update({'seasonStatus': len(guild_data_dict[post_data['name']]['seasonStatus'])})

                        self.create_or_update_player_data(data)

                    else:
                        error_list.append(f"Comlink не срабатывает: {comlink_player_request.status_code}")

                else:
                    error_list.append(f"Игрок {i['player_name']} отсутствует в гильдии. Обновите ids.json")

            print("\n".join(error_list))

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

        # получить данные за последние два дня (сегодня и вчера)
        recent_players = session.query(Player).filter(
            func.date(Player.update_time).in_([today, yesterday])
        ).all()

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

        # получить данные за последние два дня (сегодня и вчера)
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
        reid_scores.insert(0, f"Список не сдавших 600 купонов по состоянию на {update_time} {os.environ.get('TZ_SUFIX')}:\n")

        return f"\n{'-' * 30}\n".join(reid_scores)


class GuildData:
    @staticmethod
    def get_guild_data():
        guild_request = requests.get(f"http://api.swgoh.gg/guild-profile/{os.environ.get('GUILD_ID')}")
        if guild_request.status_code == 200:
            data = guild_request.json()['data']
            del data['members']
            return data

    def __set_guild_attributes(self, data):
        """Заполняет атрибуты модели гильдии"""
        guild = Guild()


def gac_statistic():
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


def split_list(input_list, parts=5):
    length = len(input_list)
    return [input_list[i * length // parts: (i + 1) * length // parts]
            for i in range(parts)]
