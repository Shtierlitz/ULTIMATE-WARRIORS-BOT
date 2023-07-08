# db_models.py
import os

from db import Base
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
    galactic_power = Column(Integer)
    required_level = Column(Integer)
    total_members = Column(Integer)
    guild_reset_time = Column(Integer)
    last_db_update_time = Column(DateTime, default=datetime.now(time_tz))
    id = Column(Integer, primary_key=True)

    def __str__(self):
        return f"{self.name}'s {self.last_db_update_time} data."


class Player(Base):
    __tablename__ = 'players'
    ally_code = Column(Integer)
    name = Column(String(100))
    level = Column(Integer)
    update_time = Column(DateTime, default=datetime.now(time_tz))     # дата обновления в бд
    guild_join_time = Column(DateTime, default=datetime.now(time_tz))
    lastActivityTime = Column(DateTime, default=datetime.now(time_tz))
    reid_points = Column(Integer)
    guild_points = Column(Integer)
    arena_rank = Column(Integer)
    url = Column(String(5000))
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    arena_leader_base_id = Column(String(50))
    last_updated = Column(DateTime, default=datetime.now(time_tz))    # дата обновления в swgoh.gg
    galactic_power = Column(Integer)
    character_galactic_power = Column(Integer)
    ship_galactic_power = Column(Integer)
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
