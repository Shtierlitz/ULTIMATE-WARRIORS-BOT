import json
import os
from datetime import datetime

from db_models import Player
from src.player_service import (
    PlayerDetailData,
    PlayerDataService,
    SwgohGuildPlayerData
)
from src.utils import get_localized_datetime


class UpdatePlayerService:

    async def update_final_data(
            self,
            player: SwgohGuildPlayerData,
            existing_players: dict,
            raw_data: json,
            swgoh_player_data: dict,
            comlink_raw_data: json
    ) -> PlayerDetailData:

        comlink_clean_data = await PlayerDataService().get_comlink_player_data(comlink_raw_data)
        comlink_player_data = await PlayerDataService().get_comlink_guild_player_data(raw_data, player.player_name)
        comlink_clean_data.comlink_galactic_power = comlink_player_data.galacticPower

        result_data = await PlayerDataService().get_swgoh_player_detail_data(swgoh_player_data)
        result_data.guild_join_time = player.guild_join_time
        result_data.existing_player = await PlayerDataService().get_existing_player_data(
            existing_players[str(player.ally_code)])
        result_data.name = comlink_clean_data.name
        result_data.level = comlink_clean_data.level
        result_data.playerId = comlink_clean_data.playerId
        result_data.lastActivityTime = comlink_clean_data.lastActivityTime
        result_data.comlink_arena_rank = comlink_clean_data.comlink_arena_rank
        result_data.comlink_fleet_arena_rank = comlink_clean_data.comlink_fleet_arena_rank
        result_data.galactic_power = comlink_clean_data.comlink_galactic_power
        result_data.season_status = len(comlink_player_data.seasonStatus)
        result_data.reid_points = comlink_player_data.memberContribution[2].currentValue
        result_data.guild_points = comlink_player_data.memberContribution[1].currentValue
        return result_data

    async def set_player_attributes(self, player: Player, data: PlayerDetailData) -> Player:
        """Устанавливает значения из переданного словаря в модель Player"""
        last_updated_utc = datetime.strptime(data.last_updated, '%Y-%m-%dT%H:%M:%S')
        player.name = data.name
        player.ally_code = data.ally_code
        player.tg_id = data.existing_player.tg_id
        player.tg_nic = data.existing_player.tg_nic
        player.update_time = datetime.now()
        player.reid_points = data.reid_points
        player.lastActivityTime = get_localized_datetime(int(data.lastActivityTime),
                                                         str(os.environ.get('TIME_ZONE')))
        player.level = data.level
        player.player_id = data.playerId
        player.arena_rank = data.comlink_arena_rank
        player.fleet_arena_rank = data.comlink_fleet_arena_rank
        player.galactic_power = int(data.galactic_power)
        player.character_galactic_power = data.character_galactic_power
        player.ship_galactic_power = data.ship_galactic_power
        player.guild_join_time = datetime.strptime(data.guild_join_time, "%Y-%m-%dT%H:%M:%S")
        player.url = 'https://swgoh.gg' + data.url
        player.last_swgoh_updated = last_updated_utc
        player.guild_currency_earned = data.guild_points
        player.arena_leader_base_id = data.arena_leader_base_id
        player.ship_battles_won = data.ship_battles_won
        player.pvp_battles_won = data.pvp_battles_won
        player.pve_battles_won = data.pve_battles_won
        player.pve_hard_won = data.pve_hard_won
        player.galactic_war_won = data.galactic_war_won
        player.guild_raid_won = data.guild_raid_won
        player.guild_exchange_donations = data.guild_exchange_donations
        player.season_status = data.season_status
        player.season_full_clears = data.season_full_clears
        player.season_successful_defends = data.season_successful_defends
        player.season_league_score = data.season_league_score
        player.season_undersized_squad_wins = data.season_undersized_squad_wins
        player.season_promotions_earned = data.season_promotions_earned
        player.season_banners_earned = data.season_banners_earned
        player.season_offensive_battles_won = data.season_offensive_battles_won
        player.season_territories_defeated = data.season_territories_defeated

        return player

    async def update_player_units(self, player: Player, units: list) -> Player:
        player.units = units
        return player
