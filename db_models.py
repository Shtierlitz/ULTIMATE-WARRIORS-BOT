# db_models.py

from db import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime


class Player(Base):
    __tablename__ = 'players'
    update_time = Column(DateTime, default=datetime.utcnow)
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    ally_code = Column(Integer)
    arena_leader_base_id = Column(String(50))
    arena_rank = Column(Integer)
    level = Column(Integer)
    name = Column(String(100))
    last_updated = Column(DateTime, default=datetime.utcnow)
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
    url = Column(String(5000))
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

    # guild_join_time = Column(DateTime, default=datetime.utcnow)

    def __str__(self):
        return f"{self.name}'s {self.update_time} data."
