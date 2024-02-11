# db_models.py
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from pytz import timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, PickleType
from sqlalchemy.orm import relationship

from settings import Base

load_dotenv()

tz = str(os.environ.get("TIME_ZONE"))
time_tz = timezone(tz)


def get_current_time_with_timezone() -> datetime:
    """Возвращает текущее время с учетом заданной временной зоны."""
    timezone = pytz.timezone(os.environ.get('TIME_ZONE'))
    date_time = datetime.now(timezone)
    date_time = date_time.replace(tzinfo=None)
    return date_time


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
    id = Column(Integer, primary_key=True)  # Идентификатор в базе
    name = Column(String(100))  # имя аккаунта
    ally_code = Column(Integer)  # код союзника
    tg_id = Column(String(100))  # идентификатор телеграма
    tg_nic = Column(String(100))  # ник в телеге
    update_time = Column(DateTime, default=get_current_time_with_timezone)  # дата обновления в бд
    reid_points = Column(String(100))  # сданые очки рейдов в день
    lastActivityTime = Column(DateTime, default=get_current_time_with_timezone)  # последний раз как заходил в игру
    level = Column(Integer)  # уровень аккаунта
    player_id = Column(String(100))  # id игрока в системе игры
    arena_rank = Column(Integer)  # ранг арены
    fleet_arena_rank = Column(Integer)  # ранг арены флота
    galactic_power = Column(Integer)  # общая галактическая мощь
    character_galactic_power = Column(Integer)  # Галактическая мощь по персонажам
    ship_galactic_power = Column(Integer)  # Галактическая мощь по флоту
    guild_join_time = Column(DateTime, default=get_current_time_with_timezone)  # дата вступления в гильдию
    url = Column(String(5000))  # ссылка на аккаунт игрока на swgoh
    last_swgoh_updated = Column(DateTime, default=get_current_time_with_timezone)  # дата обновления в swgoh.gg
    guild_currency_earned = Column(String(100))  # заработанная и собранная валюта гильдии в день
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
    units = relationship("Unit", backref="player", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.name}'s {self.update_time} data."


class UnitSkill(Base):
    __tablename__ = 'unit_skills'
    id = Column(Integer, primary_key=True)
    skill_id = Column(String(100))
    unit_id = Column(Integer, ForeignKey('units.id', ondelete="CASCADE"))
    tier = Column(Integer)
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class LevelCost(Base):
    __tablename__ = 'level_costs'
    id = Column(Integer, primary_key=True)
    bonus_quantity = Column(Integer)
    currency = Column(Integer)
    quantity = Column(Integer)
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class RemoveCost(Base):
    __tablename__ = 'remove_costs'
    id = Column(Integer, primary_key=True)
    bonus_quantity = Column(Integer)
    currency = Column(Integer)
    quantity = Column(Integer)
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class SellValue(Base):
    __tablename__ = 'sell_value'
    id = Column(Integer, primary_key=True)
    bonus_quantity = Column(Integer)
    currency = Column(Integer)
    quantity = Column(Integer)
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class InnerStat(Base):
    __tablename__ = 'inner_stats'
    id = Column(Integer, primary_key=True)
    scalar = Column(String(100))
    stat_value_decimal = Column(String(100))
    ui_display_override_value = Column(String(100))
    unit_stat_id = Column(Integer)
    unscaled_decimal_value = Column(String(100))
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class PrimaryStat(Base):
    __tablename__ = 'primary_stats'
    id = Column(Integer, primary_key=True)
    roll = Column(JSON)  # Можно хранить как JSON
    stat_id = Column(Integer, ForeignKey('inner_stats.id', ondelete="CASCADE"))
    stat_roller_bounds_max = Column(String(100))
    stat_roller_bounds_min = Column(String(100))
    stat_rolls = Column(Integer)
    unscaled_roll_value = Column(JSON)  # Можно хранить как JSON
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class UnitMod(Base):
    __tablename__ = 'unit_mods'
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey('units.id', ondelete="CASCADE"))
    mod_id = Column(String(100))
    bonus_quantity = Column(Integer)
    definition_id = Column(String(100))
    level = Column(Integer)
    level_cost = Column(Integer, ForeignKey('level_costs.id', ondelete="CASCADE"))
    locked = Column(Boolean)
    primary_stat = Column(Integer, ForeignKey('primary_stats.id', ondelete="CASCADE"))
    remove_cost = Column(Integer, ForeignKey('remove_costs.id', ondelete="CASCADE"))
    rerolled_count = Column(Integer)
    secondary_stats = relationship(
        "SecondaryStat",
        backref="unit_mod",
        foreign_keys="[SecondaryStat.unit_mod_id]",
        lazy='noload'
    )
    sell_value = Column(JSON)  # Можно хранить как JSON
    tier = Column(Integer)
    xp = Column(Integer)
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class SecondaryStat(Base):
    __tablename__ = 'secondary_stats'
    id = Column(Integer, primary_key=True)
    roll = Column(JSON)  # Можно хранить как JSON
    stat_id = Column(Integer, ForeignKey('inner_stats.id', ondelete="CASCADE"))
    stat_roller_bounds_max = Column(String(100))
    stat_roller_bounds_min = Column(String(100))
    stat_rolls = Column(Integer)
    unscaled_roll_value = Column(JSON)
    unit_mod_id = Column(Integer, ForeignKey('unit_mods.id', ondelete="CASCADE"))  # Добавленный внешний ключ
    update_time = Column(DateTime, default=get_current_time_with_timezone)


class Unit(Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    unit_id = Column(String(100))
    player_id = Column(Integer, ForeignKey('players.id', ondelete="CASCADE"))
    definition_id = Column(String(100))
    current_stars = Column(String(100))
    current_level = Column(Integer)
    current_rarity = Column(Integer)
    current_tier = Column(Integer)
    current_xp = Column(Integer)
    equipment = Column(JSON)  # Можно хранить как JSON
    equipped_stat_mod_old = Column(JSON)  # Можно хранить как JSON
    promotion_recipe_reference = Column(String(100))
    purchased_ability_id = Column(JSON)  # Можно хранить как JSON
    relic = Column(JSON)  # Можно хранить как JSON
    # Отношения с другими таблицами
    equipped_stat_mod = relationship("UnitMod", backref="unit", lazy='noload')
    skill = relationship("UnitSkill", backref="unit", lazy='noload')
    update_time = Column(DateTime, default=get_current_time_with_timezone)
    unit_stat = Column(PickleType, nullable=True, default=None)
