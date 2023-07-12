# db_models.py
import os

from settings import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

load_dotenv()

tz = str(os.environ.get("TIME_ZONE"))
time_tz = timezone(tz)



class Guild(Base):
    __tablename__ = 'guild'
    name = Column(String(50))
    guild_id = Column(String(500))
    credo = Column(String(500))
    galactic_power = Column(String(500))
    required_level = Column(Integer)
    total_members = Column(Integer)
    guild_reset_time = Column(DateTime, default=datetime.now())
    last_db_update_time = Column(DateTime, default=datetime.now(time_tz))
    id = Column(Integer, primary_key=True)

    def __str__(self):
        return f"{self.name}'s {self.last_db_update_time} data."


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)      # Идентификатор в базе
    name = Column(String(100))                  # имя аккаунта
    ally_code = Column(Integer)               # код союзника
    tg_id = Column(String(100))                   # идентификатор телеграма
    tg_nic = Column(String(100))                # ник в телеге
    update_time = Column(DateTime, default=datetime.now())  # дата обновления в бд
    reid_points = Column(String(100))             # сданые очки рейдов в день
    lastActivityTime = Column(DateTime, default=datetime.now())  # последний раз как заходил в игру
    level = Column(Integer)                     # уровень аккаунта
    player_id = Column(String(100))                 # id игрока в системе игры
    arena_rank = Column(Integer)               # ранг арены
    galactic_power = Column(Integer)            # общая галактическая мощь
    character_galactic_power = Column(Integer)    # Галактическая мощь по персонажам
    ship_galactic_power = Column(Integer)         # Галактическая мощь по флоту
    guild_join_time = Column(DateTime, default=datetime.now())   # дата вступления в гильдию
    url = Column(String(5000))                  # ссылка на аккаунт игрока на swgoh
    last_swgoh_updated = Column(DateTime, default=datetime.now())  # дата обновления в swgoh.gg
    guild_currency_earned = Column(String(100))        # заработанная и собранная валюта гильдии в день
    arena_leader_base_id = Column(String(50))
    ship_battles_won = Column(Integer)
    pvp_battles_won = Column(Integer)
    pve_battles_won = Column(Integer)
    pve_hard_won = Column(Integer)
    galactic_war_won = Column(Integer)
    guild_raid_won = Column(Integer)
    guild_exchange_donations = Column(Integer)
    season_status = Column(Integer)
    season_full_clears = Column(Integer)
    season_successful_defends = Column(Integer)
    season_league_score = Column(Integer)
    season_undersized_squad_wins = Column(Integer)
    season_promotions_earned = Column(Integer)
    season_banners_earned = Column(Integer)
    season_offensive_battles_won = Column(Integer)
    season_territories_defeated = Column(Integer)

    def __str__(self):
        return f"{self.name}'s {self.update_time} data."
