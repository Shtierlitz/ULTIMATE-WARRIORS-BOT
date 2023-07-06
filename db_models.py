# db_models.py

from db import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime


class Guild(Base):
    __tablename__ = 'guild'
    name = Column(String(50))
    external_message = Column(String(500))
    galactic_power = Column(Integer)
    level_requirement = Column(Integer)
    member_count = Column(Integer)
    avg_galactic_power = Column(Integer)
    avg_arena_rank = Column(Integer)
    avg_fleet_arena_rank = Column(Integer)
    avg_skill_rating = Column(Integer)
    last_sync = Column(DateTime, default=datetime.utcnow)
    guild_id = Column(String(500))
    enrollment_status = Column(Integer)
    banner_color_id = Column(String(50))
    banner_logo_id = Column(String(50))
    guild_type = Column(Integer)
    id = Column(Integer, primary_key=True)

    def __str__(self):
        return f"{self.name}'s {self.update_time} data."


class Player(Base):
    __tablename__ = 'players'
    ally_code = Column(Integer)
    name = Column(String(100))
    level = Column(Integer)
    update_time = Column(DateTime, default=datetime.utcnow)     # дата обновления в бд
    guild_join_time = Column(DateTime, default=datetime.utcnow)
    arena_rank = Column(Integer)
    url = Column(String(5000))
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    arena_leader_base_id = Column(String(50))
    last_updated = Column(DateTime, default=datetime.utcnow)    # дата обновления в swgoh.gg
    galactic_power = Column(Integer)
    character_galactic_power = Column(Integer)
    ship_galactic_power = Column(Integer)
    ship_battles_won = Column(Integer)
    pvp_battles_won = Column(Integer)
    pve_battles_won = Column(Integer)
    pve_hard_won = Column(Integer)
    galactic_war_won = Column(Integer)
    guild_raid_won = Column(Integer)
    guild_contribution = Column(Integer)
    guild_exchange_donations = Column(Integer)
    season_full_clears = Column(Integer)
    season_successful_defends = Column(Integer)
    season_league_score = Column(Integer)
    season_undersized_squad_wins = Column(Integer)
    season_promotions_earned = Column(Integer)
    season_banners_earned = Column(Integer)
    season_offensive_battles_won = Column(Integer)
    season_territories_defeated = Column(Integer)
    skill_rating = Column(Integer)
    division_number = Column(Integer)
    league_name = Column(String(100))
    league_frame_image = Column(String(5000))
    league_blank_image = Column(String(5000))
    league_image = Column(String(5000))
    division_image = Column(String(5000))
    portrait_image = Column(String(5000))
    title = Column(String(100))
    guild_id = Column(String(100))
    guild_name = Column(String(100))
    guild_url = Column(String(100))

    def __str__(self):
        return f"{self.name}'s {self.update_time} data."
