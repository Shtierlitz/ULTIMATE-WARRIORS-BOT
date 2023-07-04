# api_utils.py
import json

import requests
from sqlalchemy import func

from create_bot import session
from datetime import datetime, timedelta
from db_models import Player


def get_players_ally_code(player_name):
    pass


def player_data_by_code(ally_code: int):
    player_search = requests.get(f'http://api.swgoh.gg/player/{ally_code}/')
    if player_search.status_code == 200:
        data = player_search.json()
        return data['data']


def add_ids():
    with open("./api/ids.json", encoding="utf-8") as f:
        data = json.load(f)  # Загрузить список словарей

    result = {}  # Создать пустой словарь

    for d in data:  # Пройтись по всем словарям в списке
        for key, value in d.items():  # Пройтись по всем парам ключ-значение в словаре
            result[key] = value  # Добавить ключ и значение в результат

    return result


def create_or_update_player_data(data: dict):
    """Создает или обновляет данные пользователя на текущий день"""
    # Проверка наличия пользователя в базе данных
    existing_user_today = session.query(Player).filter_by(name=data['name']).filter(
        func.date(Player.update_time) == datetime.today().date()).first()
    existing_user_older = session.query(Player).filter_by(name=data['name']).filter(
        func.date(Player.update_time) < datetime.today().date()).first()

    ids = add_ids()
    # Если пользователь уже существует

    if existing_user_today:
        # Обновляем данные пользователя
        existing_user_today.player_id = ids[data['name']]
        existing_user_today.update_time = datetime.utcnow()
        existing_user_today.ally_code = data['ally_code']
        existing_user_today.arena_leader_base_id = data['arena_leader_base_id']
        existing_user_today.arena_rank = data['arena_rank']
        existing_user_today.level = data['level']
        existing_user_today.last_updated = datetime.strptime(data['last_updated'], '%Y-%m-%dT%H:%M:%S')
        existing_user_today.galactic_power = data['galactic_power']
        existing_user_today.character_galactic_power = data['character_galactic_power']
        existing_user_today.ship_battles_won = data['ship_battles_won']
        existing_user_today.pvp_battles_won = data['pvp_battles_won']
        existing_user_today.pve_battles_won = data['pve_battles_won']
        existing_user_today.pve_hard_won = data['pve_hard_won']
        existing_user_today.galactic_war_won = data['galactic_war_won']
        existing_user_today.guild_raid_won = data['guild_raid_won']
        existing_user_today.guild_contribution = data['guild_contribution']
        existing_user_today.guild_exchange_donations = data['guild_exchange_donations']
        existing_user_today.season_full_clears = data['season_full_clears']
        existing_user_today.season_successful_defends = data['season_successful_defends']
        existing_user_today.season_league_score = data['season_league_score']
        existing_user_today.season_undersized_squad_wins = data['season_undersized_squad_wins']
        existing_user_today.season_promotions_earned = data['season_promotions_earned']
        existing_user_today.season_banners_earned = data['season_banners_earned']
        existing_user_today.season_offensive_battles_won = data['season_offensive_battles_won']
        existing_user_today.season_territories_defeated = data['season_territories_defeated']
        existing_user_today.url = 'https://swgoh.gg' + data['url']
        existing_user_today.skill_rating = data['skill_rating']
        existing_user_today.division_number = data['division_number']
        existing_user_today.league_name = data['league_name']
        existing_user_today.league_frame_image = data['league_frame_image']
        existing_user_today.league_blank_image = data['league_blank_image']
        existing_user_today.league_image = data['league_image']
        existing_user_today.division_image = data['division_image']
        existing_user_today.portrait_image = data['portrait_image']
        existing_user_today.title = data['title']
        existing_user_today.guild_id = data['guild_id']
        existing_user_today.guild_name = data['guild_name']
        existing_user_today.guild_url = 'https://swgoh.gg' + data['guild_url']
        session.commit()
    elif existing_user_older:
        # Добавляем нового пользователя
        new_user = Player(
            player_id=ids[data['name']],
            ally_code=data['ally_code'],
            arena_leader_base_id=data['arena_leader_base_id'],
            arena_rank=data['arena_rank'],
            level=data['level'],
            name=data['name'],
            last_updated=datetime.strptime(data['last_updated'], '%Y-%m-%dT%H:%M:%S'),
            galactic_power=data['galactic_power'],
            character_galactic_power=data['character_galactic_power'],
            ship_galactic_power=data['ship_galactic_power'],
            ship_battles_won=data['ship_battles_won'],
            pvp_battles_won=data['pvp_battles_won'],
            pve_battles_won=data['pve_battles_won'],
            pve_hard_won=data['pve_hard_won'],
            galactic_war_won=data['galactic_war_won'],
            guild_raid_won=data['guild_raid_won'],
            guild_contribution=data['guild_contribution'],
            guild_exchange_donations=data['guild_exchange_donations'],
            season_full_clears=data['season_full_clears'],
            season_successful_defends=data['season_successful_defends'],
            season_league_score=data['season_league_score'],
            season_undersized_squad_wins=data['season_undersized_squad_wins'],
            season_promotions_earned=data['season_promotions_earned'],
            season_banners_earned=data['season_banners_earned'],
            season_offensive_battles_won=data['season_offensive_battles_won'],
            season_territories_defeated=data['season_territories_defeated'],
            url='https://swgoh.gg' + data['url'],
            skill_rating=data['skill_rating'],
            division_number=data['division_number'],
            league_name=data['league_name'],
            league_frame_image=data['league_frame_image'],
            league_blank_image=data['league_blank_image'],
            league_image=data['league_image'],
            division_image=data['division_image'],
            portrait_image=data['portrait_image'],
            title=data['title'],
            guild_id=data['guild_id'],
            guild_name=data['guild_name'],
            guild_url=data['guild_url'],
        )
        session.add(new_user)
        session.commit()

        # Удаление записей старше месяца
    month_old_date = datetime.now() - timedelta(days=30)
    session.query(Player).filter(Player.update_time < month_old_date).delete()
    session.commit()


def update_players_data():
    """Вытаскивает данные о гильдии и участниках, а после
     по имени участника гоняет циклом обновление бд для каждого участника"""
    guild_profile = requests.get("http://api.swgoh.gg/guild-profile/0rNNFa76RXyv0C3suyUkFA")
    if guild_profile.status_code == 200:
        data = guild_profile.json()
        for i in data['data']['members']:
            data = player_data_by_code(i['ally_code'])
            create_or_update_player_data(data)


def extract_data(player: Player):
    """Выводит все данные по игроку"""
    data_dict = player.__dict__
    formatted_string = "\n".join(f"{key}: {value}\n{'-'*30}" for key, value in data_dict.items() if not key.startswith('_'))
    return formatted_string


def get_player_filtered_data(data: Player, key: str):
    """Возвращает данные игрока по ключу"""
    return data.__dict__[key]
