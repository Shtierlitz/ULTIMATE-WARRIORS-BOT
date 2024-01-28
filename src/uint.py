from pprint import pprint

from src.player import PlayerData, PlayerService
from src.player_service import PlayerDataService
from src.roster_unit_service import RosterDataService, CreateUnitService


class UnitUpdateService:

    ROSTER_DATA_SERVICE = RosterDataService
    PLAYER_DATA = PlayerData
    PLAYER_SERVICE = PlayerService
    PLAYER_DATA_SERVICE = PlayerDataService
    CREATE_UNIT_SERVICE = CreateUnitService

    async def create_unit_db(self):
        """Создание юнита в БД"""
        ally_codes = await self.PLAYER_DATA().get_today_players_ally_codes()
        for ally_code in ally_codes:
            player_id = await self.PLAYER_DATA().get_today_player_id(ally_code)
            comlink_raw_data = await PlayerService().get_comlink_player(ally_code)
            roster_data = await self.ROSTER_DATA_SERVICE().get_roster_data(comlink_raw_data['rosterUnit'])
            units = []
            for roster_unit in roster_data:
                units.append(await self.CREATE_UNIT_SERVICE(roster_unit, player_id).update_today_units())

            await self.PLAYER_DATA().update_players_units(player_id, units)

