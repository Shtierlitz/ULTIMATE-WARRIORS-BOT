# api_utils.py
import json
import os

import requests
from sqlalchemy import func

from create_bot import session
from datetime import datetime, timedelta

from db_models import Player, Guild


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
        ids = self.__add_ids()

        player.name = data['name']
        player.guild_join_time = datetime.strptime(data['guild_join_time'], '%Y-%m-%dT%H:%M:%S')
        player.player_id = ids[data['name']]
        player.update_time = datetime.utcnow()
        player.ally_code = data['ally_code']
        player.arena_leader_base_id = data['arena_leader_base_id']
        player.arena_rank = data['arena_rank']
        player.level = data['level']
        player.last_updated = datetime.strptime(data['last_updated'], '%Y-%m-%dT%H:%M:%S')
        player.galactic_power = data['galactic_power']
        player.character_galactic_power = data['character_galactic_power']
        player.ship_galactic_power = data['ship_galactic_power']
        player.ship_battles_won = data['ship_battles_won']
        player.pvp_battles_won = data['pvp_battles_won']
        player.pve_battles_won = data['pve_battles_won']
        player.pve_hard_won = data['pve_hard_won']
        player.galactic_war_won = data['galactic_war_won']
        player.guild_raid_won = data['guild_raid_won']
        player.guild_contribution = data['guild_contribution']
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
        player.skill_rating = data['skill_rating']
        player.division_number = data['division_number']
        player.league_name = data['league_name']
        player.league_frame_image = data['league_frame_image']
        player.league_blank_image = data['league_blank_image']
        player.league_image = data['league_image']
        player.division_image = data['division_image']
        player.portrait_image = data['portrait_image']
        player.title = data['title']
        player.guild_id = data['guild_id']
        player.guild_name = data['guild_name']
        player.guild_url = 'https://swgoh.gg' + data['guild_url']

        return player

    def update_players_data(self):
        """Вытаскивает данные о гильдии и участниках, а после
         по имени участника гоняет циклом обновление бд для каждого участника"""

        guild_request = requests.get(f"http://api.swgoh.gg/guild-profile/{os.environ.get('GUILD_ID')}")
        if guild_request.status_code == 200:
            data = guild_request.json()
            for i in data['data']['members']:
                data: dict = self.player_data_by_code(i['ally_code'])
                data.update({'guild_join_time': i['guild_join_time']})
                self.create_or_update_player_data(data)

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
    return f'\n{"-" * 30}\n'.join(st_1), f'\n{"-" * 30}\n'.join(st_2), f'\n{"-" * 30}\n'.join(st_3), f'\n{"-" * 30}\n'.join(st_4), f'\n{"-" * 30}\n'.join(st_5)


def split_list(input_list, parts=5):
    length = len(input_list)
    return [input_list[i * length // parts: (i + 1) * length // parts]
            for i in range(parts)]
