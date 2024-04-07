import json
from pprint import pprint

from src.player import PlayerData, PlayerService
from src.player_service import PlayerDataService
from src.roster_unit_service import RosterDataService, CreateUnitService


class UnitAggregateService:
    async def create_or_update_unit(self):
        """Создание юнита в БД"""
        localization_data = await self.load_localization_data()
        ally_codes = await PlayerData().get_today_players_ally_codes()
        print(len(ally_codes))
        counter = 0
        for ally_code in ally_codes:
            player_id = await PlayerData().get_today_player_id(ally_code)
            comlink_raw_data = await PlayerService().get_comlink_player(ally_code)
            roster_data = await RosterDataService().get_roster_data(comlink_raw_data['rosterUnit'], localization_data)
            # pprint(roster_data)
            units = []
            for roster_unit in roster_data:
                units.append(await CreateUnitService(roster_unit, player_id).update_today_units())

            await PlayerData().update_players_units(player_id, units)
            counter += 1
            print(counter)
        print(f"Юниты {counter} игроков обновлены.")

    async def load_localization_data(self):
        with open('localization.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
