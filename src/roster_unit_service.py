import json
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import Any, Optional
from settings import Base
from db_models import (
    Unit,
    UnitMod,
    UnitSkill,
    LevelCost,
    RemoveCost,
    SellValue,
    PrimaryStat,
    InnerStat,
    SecondaryStat
)
from settings import async_session_maker
from src.utils import get_new_day_start
from sqlalchemy import (
    select,
)


@dataclass
class UnitSkills:
    id: str
    tier: int


@dataclass
class CostData:
    bonusQuantity: int
    currency: int
    quantity: int


@dataclass
class InnerStatData:
    scalar: str
    statValueDecimal: str
    uiDisplayOverrideValue: str
    unitStatId: int
    unscaledDecimalValue: str


@dataclass
class SecondaryStatData:
    roll: list
    stat: InnerStatData
    statRollerBoundsMax: str
    statRollerBoundsMin: str
    statRolls: int
    unscaledRollValue: list


@dataclass
class PrimaryStatData:
    roll: list[str]
    stat: InnerStatData
    statRollerBoundsMax: str
    statRollerBoundsMin: str
    statRolls: int
    unscaledRollValue: list


@dataclass
class UnitModsData:
    bonusQuantity: int
    definitionId: str
    mod_id: str
    level: int
    levelCost: CostData
    locked: bool
    primaryStat: PrimaryStatData
    removeCost: CostData
    rerolledCount: int
    secondaryStat: list[SecondaryStatData]
    sellValue: CostData
    tier: int
    xp: int
    convertedItem: Optional[Any] = None


@dataclass
class UnitSkillData:
    id: str
    tier: int


@dataclass
class RosterUnitData:
    player_id: int
    definitionId: str
    currentLevel: int
    currentRarity: int
    currentTier: int
    currentXp: int
    equipment: list[dict]
    equippedStatModOld: list
    unit_id: str
    promotionRecipeReference: str
    purchasedAbilityId: list
    relic: dict
    equippedStatMod: list[UnitModsData] = None
    skill: list[UnitSkillData] = None
    unitStat: Optional[Any] = None


class RosterDataService:
    def __init__(self, player_id: int = None):
        self.pk = player_id

    async def get_roster_data(self, data: list[json]) -> list[RosterUnitData]:
        return [
            await self.get_roster_unit_data(item)
            for item in data
        ]

    async def get_roster_unit_data(self, data: json) -> RosterUnitData:
        return RosterUnitData(
            player_id=self.pk,
            definitionId=data['definitionId'],
            currentLevel=data['currentLevel'],
            currentRarity=data['currentRarity'],
            currentTier=data['currentTier'],
            currentXp=data['currentXp'],
            equipment=data['equipment'],
            equippedStatMod=await self.get_unit_mods_data(data['equippedStatMod']),
            equippedStatModOld=data['equippedStatModOld'],
            unit_id=data['id'],
            promotionRecipeReference=data['promotionRecipeReference'],
            purchasedAbilityId=data['purchasedAbilityId'],
            relic=data['relic'],
            skill=await self.get_unit_skill_data(data['skill']),
            unitStat=data['unitStat']
        )

    async def get_unit_skill_data(self, data: json) -> list[UnitSkillData]:
        return [
            UnitSkillData(
                id=item['id'],
                tier=item['tier']
            )
            for item in data
        ]

    async def get_unit_mods_data(self, data: list[json]) -> list[UnitModsData]:
        return [
            UnitModsData(
                bonusQuantity=item['bonusQuantity'],
                convertedItem=item['convertedItem'],
                definitionId=item['definitionId'],
                mod_id=item['id'],
                level=item['level'],
                levelCost=await self.get_level_cost_data(item['levelCost']),
                locked=item['locked'],
                primaryStat=await self.get_primary_stat_data(item['primaryStat']),
                removeCost=await self.get_level_cost_data(item['removeCost']),
                rerolledCount=item['rerolledCount'],
                secondaryStat=await self.get_secondary_stat_data(item['secondaryStat']),
                sellValue=await self.get_level_cost_data(item['sellValue']),
                tier=item['tier'],
                xp=item['xp']
            )
            for item in data
        ]

    async def get_secondary_stat_data(self, data: list[json]) -> list[SecondaryStatData]:
        return [
            SecondaryStatData(
                roll=item['roll'],
                stat=await self.get_inner_stat_data(item['stat']),
                statRollerBoundsMax=item['statRollerBoundsMax'],
                statRollerBoundsMin=item['statRollerBoundsMin'],
                statRolls=item['statRolls'],
                unscaledRollValue=item['unscaledRollValue']
            )
            for item in data
        ]

    async def get_primary_stat_data(self, data: json) -> PrimaryStatData:
        return PrimaryStatData(
            roll=data['roll'],
            stat=await self.get_inner_stat_data(data['stat']),
            statRollerBoundsMax=data['statRollerBoundsMax'],
            statRollerBoundsMin=data['statRollerBoundsMin'],
            statRolls=data['statRolls'],
            unscaledRollValue=data['unscaledRollValue']
        )

    async def get_inner_stat_data(self, data: json) -> InnerStatData:
        return InnerStatData(
            scalar=data['scalar'],
            statValueDecimal=data['statValueDecimal'],
            uiDisplayOverrideValue=data['uiDisplayOverrideValue'],
            unitStatId=data['unitStatId'],
            unscaledDecimalValue=data['unscaledDecimalValue']
        )

    async def get_level_cost_data(self, data: json) -> CostData:
        return CostData(
            bonusQuantity=data['bonusQuantity'],
            currency=data['currency'],
            quantity=data['quantity']
        )


class CreateUnitService:
    def __init__(self, roster_data: RosterUnitData, player_id: int):
        self.roster_data = roster_data
        self.player_id = player_id

    async def update_today_units(self) -> Unit:
        new_day_start = get_new_day_start()
        async with async_session_maker() as session:
            query = await session.execute(
                select(Unit).filter_by(player_id=self.roster_data.player_id).filter(
                    Unit.update_time >= new_day_start))
            existing_units_today = query.scalars().all()

            if existing_units_today:
                for unit in existing_units_today:
                    new_unit = await self.set_unit_attributes(unit)
                    await session.update(new_unit)
                    await session.commit()
            else:
                new_unit = await self.set_unit_attributes(Unit())
                if new_unit:
                    session.add(new_unit)
                    await session.commit()
                    return new_unit

    async def set_unit_attributes(self, unit: Unit) -> Unit:
        """Устанавливает значения из переданного словаря в модель Unit"""
        data = self.roster_data
        unit.player_id = self.player_id
        unit.unit_id = data.unit_id
        unit.definitionId = data.definitionId
        unit.currentLevel = data.currentLevel
        unit.currentRarity = data.currentRarity
        unit.currentTier = data.currentTier
        unit.currentXp = data.currentXp
        unit.equipment = data.equipment
        unit.equippedStatMod = await self.get_or_create_unit_mods(unit)
        unit.equippedStatModOld = data.equippedStatModOld
        unit.promotionRecipeReference = data.promotionRecipeReference
        unit.purchasedAbilityId = data.purchasedAbilityId
        unit.relic = data.relic
        unit.skill = await self.get_or_create_unit_skills(unit)
        unit.unitStat = data.unitStat
        unit.update_time = datetime.now()
        return unit

    async def get_or_create_unit_skills(self, unit: Unit) -> list[UnitSkill]:
        """Получаем или создаем скилы для юнита"""
        new_day_start = get_new_day_start()
        async with async_session_maker() as session:
            query = await session.execute(
                select(UnitSkill).filter_by(unit_id=unit.id).filter(
                    UnitSkill.update_time >= new_day_start))
            unit_skills = query.scalars().all()
            if unit_skills:
                return unit_skills
            if unit_skills:
                unit_skills = await self.create_unit_skils(unit)
                await session.add_all(unit_skills)
                await session.commit()
                return unit_skills
            return []

    async def create_unit_skils(self, unit: Unit) -> list[UnitSkill]:
        return [
            UnitSkill(
                unit_id=unit.id,
                skill_id=item.id,
                tier=item.tier
            )
            for item in self.roster_data.skill
        ]

    async def get_or_create_unit_mods(self, unit: Unit) -> list[UnitMod]:
        """Получаем или создаем моды для юнита"""
        new_day_start = get_new_day_start()
        async with async_session_maker() as session:
            query = await session.execute(
                select(UnitMod).filter_by(unit_id=unit.id).filter(
                    UnitMod.update_time >= new_day_start))
            unit_mods = query.scalars().all()
            if unit_mods:
                return unit_mods
            unit_mods = await self.create_unit_mods(unit)
            if unit_mods:
                session.add_all(unit_mods)
                await session.commit()
                return unit_mods
            return []

    async def create_unit_mods(self, unit: Unit) -> list[UnitMod]:
        data = [
            UnitMod(
                unit_id=unit.id,
                mod_id=item.mod_id,
                bonus_quantity=item.bonusQuantity,
                definition_id=item.definitionId,
                level=item.level,
                level_cost=await self.create_costs(item.levelCost, LevelCost),
                locked=item.locked,
                primary_stat=await self.create_primary_stat(item.primaryStat),
                remove_cost=await self.create_costs(item.removeCost, RemoveCost),
                rerolled_count=item.rerolledCount,
                secondary_stats=await self.create_secondary_stat(item.secondaryStat),
                sell_value=await self.create_costs(item.sellValue, SellValue),
                tier=item.tier,
                xp=item.xp
            )
            for item in self.roster_data.equippedStatMod
        ]
        return data

    async def create_costs(self, data: CostData, model: Base) -> int:
        async with async_session_maker() as session:
            cost_record = model(
                bonus_quantity=data.bonusQuantity,
                currency=data.currency,
                quantity=data.quantity,
            )
            session.add(cost_record)
            await session.commit()
            await session.refresh(cost_record)
            return cost_record.id

    async def create_primary_stat(self, data: PrimaryStatData) -> int:
        async with async_session_maker() as session:
            stat_record = PrimaryStat(
                roll=data.roll,
                stat_id=await self.create_inner_stat(data.stat),
                stat_roller_bounds_max=data.statRollerBoundsMax,
                stat_roller_bounds_min=data.statRollerBoundsMin,
                stat_rolls=data.statRolls,
                unscaled_roll_value=data.unscaledRollValue
            )
            session.add(stat_record)
            await session.commit()
            await session.refresh(stat_record)
            return stat_record.id

    async def create_inner_stat(self, data: InnerStatData) -> int:
        async with async_session_maker() as session:
            stat_record = InnerStat(
                scalar=data.scalar,
                stat_value_decimal=data.statValueDecimal,
                ui_display_override_value=data.uiDisplayOverrideValue,
                unit_stat_id=data.unitStatId,
                unscaled_decimal_value=data.unscaledDecimalValue
            )
            session.add(stat_record)
            await session.commit()
            await session.refresh(stat_record)
            return stat_record.id

    async def create_secondary_stat(self, data: list[SecondaryStatData]) -> list[SecondaryStat]:
        async with async_session_maker() as session:
            stat_records = [
                SecondaryStat(
                    roll=item.roll,
                    stat_id=await self.create_inner_stat(item.stat),
                    stat_roller_bounds_max=item.statRollerBoundsMax,
                    stat_roller_bounds_min=item.statRollerBoundsMin,
                    stat_rolls=item.statRolls,
                    unscaled_roll_value=item.unscaledRollValue
                ) for item in data
            ]
            if stat_records:
                session.add_all(stat_records)
                await session.commit()
                return stat_records
            return []
