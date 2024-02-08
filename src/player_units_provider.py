from __future__ import annotations

from dataclasses import dataclass
from pprint import pprint

from aiogram import types
from aiogram.types import Message
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload

from create_bot import bot
from db_models import Player
from settings import async_session_maker
from src.roster_unit_service import RosterUnitData


@dataclass
class UnitStatsData:
    name: str
    stars: int
    level: int
    tier: int
    relic: int | None
    xp: int


class PlayerUnitDataService:
    async def get_units_data(self, player: Player) -> list[RosterUnitData]:
        return [
            RosterUnitData(
                player_id=unit.player_id,
                definitionId=unit.definition_id,
                currentLevel=unit.current_level,
                currentRarity=unit.current_rarity,
                currentTier=unit.current_tier,
                currentXp=unit.current_xp,
                equipment=unit.equipment,
                equippedStatModOld=unit.equipped_stat_mod_old,
                unit_id=unit.unit_id,
                promotionRecipeReference=unit.promotion_recipe_reference,
                purchasedAbilityId=unit.purchased_ability_id,
                relic=unit.relic
            )
            for unit in player.units
        ]

    async def get_unit_stats_data(self, unit: RosterUnitData) -> UnitStatsData:
        return UnitStatsData(
            name=await self.create_unit_name(unit.definitionId),
            stars=await self.create_unit_stars(unit.definitionId),
            level=unit.currentLevel,
            tier=unit.currentTier,
            relic=await self.create_unit_tier(unit.relic),
            xp=unit.currentXp
        )

    async def create_unit_tier(self, tier: dict) -> int | None:
        if not tier:
            return
        return await self.create_unit_relic(tier['currentTier'])

    async def create_unit_name(self, definition_id: str):
        return definition_id.split(':')[0]

    async def create_unit_stars(self, definition_id: str) -> int:
        star_mapping = {
            'SEVEN_STAR': 7,
            'SIX_STAR': 6,
            'FIVE_STAR': 5,
            'FOUR_STAR': 4,
            'THREE_STAR': 3,
            'TWO_STAR': 2,
            'ONE_STAR': 1,
        }
        string = definition_id.split(':')[1]
        return star_mapping.get(string, 0)

    async def create_unit_relic(self, relic: int) -> int:
        relic_mapping = {
            1: None,
            2: 0,
            3: 1,
            4: 2,
            5: 3,
            6: 4,
            7: 5,
            8: 6,
            9: 7,
            10: 8,
            11: 9,
        }
        return relic_mapping.get(relic, 0)

    async def get_unit_data_by_name(self, player: Player, name_part: str) -> list[UnitStatsData]:
        units = await self.get_units_data(player)
        unit_list = []
        for unit in units:
            unit_stats = await self.get_unit_stats_data(unit)
            if name_part.lower() in unit_stats.name.lower():
                unit_list.append(unit_stats)
        return unit_list


class PlayerUnitsProvider:
    async def get_units(self, message: Message, player_name: str):
        """Получает список персонажей игрока"""
        try:
            player = await self.get_player(player_name)
        except Exception as e:
            await bot.send_message(
                message.chat.id,
                 f"❌ Игрок с именем {player_name} отсутствует\n"
                 f"Проверьте правильность написания имени"
            )
            return
        units = await PlayerUnitDataService().get_unit_data_by_name(player, 'han')
        return await self.convert_unit_data_to_message(units)

    async def convert_unit_data_to_message(self, units: list[UnitStatsData]):
        """Конвертирует данные персонажей в сообщение"""
        message = ''
        for unit in units:
            message += f"{unit.name},\nЗвезды: {unit.stars}, Уровень: {unit.level}, " \
                       f"Тир: {unit.tier}, Рел: {unit.relic if unit.relic is not None else 'нету'}, " \
                    f"ГМ: {unit.xp}\n\n"
        return message

    async def get_player(self, player_name: str):
        async with async_session_maker() as session:
            result = await session.execute(
                select(Player)
                .where(Player.name == player_name)
                .options(joinedload(Player.units))
                .order_by(desc(Player.update_time))
            )
            player = result.scalars().first()
            return player


