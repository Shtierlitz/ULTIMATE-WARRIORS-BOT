import json
from dataclasses import dataclass


@dataclass
class ArenaData:
    leader: str
    members: list[str]
    rank: int
    reinforcements: list[str] = None


@dataclass
class ExistingPlayer:
    player_name: str
    tg_id: str
    tg_nic: str


@dataclass
class PlayerDetailData:
    name: str
    ally_code: int
    arena: ArenaData
    arena_leader_base_id: str
    arena_rank: int
    character_galactic_power: int
    division_image: str
    division_number: int
    fleet_arena: ArenaData
    galactic_power: int
    galactic_war_won: int
    guild_contribution: int
    guild_exchange_donations: int
    guild_id: str
    guild_name: str
    guild_raid_won: int
    guild_url: str
    last_updated: str
    league_blank_image: str
    league_frame_image: str
    league_image: str
    league_name: str
    level: str
    mods: list
    portrait_image: str
    pve_battles_won: int
    pve_hard_won: int
    pvp_battles_won: int
    season_banners_earned: int
    season_full_clears: int
    season_league_score: int
    season_offensive_battles_won: int
    season_promotions_earned: int
    season_successful_defends: int
    season_territories_defeated: int
    season_undersized_squad_wins: int
    ship_battles_won: int
    ship_galactic_power: int
    skill_rating: int
    title: str
    url: str
    guild_join_time: str = None
    existing_player: ExistingPlayer = None
    tg_id: str = None
    tg_nic: str = None
    update_time: str = None
    reid_points: str = None
    lastActivityTime: str = None
    comlink_arena_rank: str = None
    comlink_fleet_arena_rank: str = None
    season_status: str = None
    guild_points: str = None
    playerId: str = None


@dataclass
class ComlinkPlayerData:
    name: str
    level: str
    playerId: str
    lastActivityTime: str
    comlink_arena_rank: str
    comlink_fleet_arena_rank: str
    comlink_galactic_power: str = None


@dataclass
class MemberContribution:
    currentValue: str
    lifetimeValue: str
    type: int


@dataclass
class SeasonStatusData:
    division: int
    endTime: str
    eventInstanceId: str
    joinTime: str
    league: str
    losses: int
    rank: int
    remove: bool
    seasonId: str
    seasonPoints: int
    wins: int


@dataclass
class ComlinkGuildPlayerData:
    playerName: str
    characterGalacticPower: str
    galacticPower: str
    guildJoinTime: str
    guildXp: int
    lastActivityTime: str
    leagueId: str
    lifetimeSeasonScore: str
    memberContribution: list[MemberContribution]
    memberLevel: int
    playerId: str
    playerLevel: int
    playerPortrait: str
    playerTitle: str
    seasonStatus: list[SeasonStatusData]
    shipGalacticPower: str
    squadPower: int


@dataclass
class SwgohGuildPlayerData:
    player_name: str
    ally_code: int
    galactic_power: int
    guild_join_time: str
    league_frame_image: str
    league_id: str
    league_name: str
    lifetime_season_score: str
    member_level: int
    player_level: int
    portrait_image: str
    squad_power: int
    title: str


class PlayerDataService:
    async def get_existing_player_data(self, data: json):
        return ExistingPlayer(
            player_name=data['player_name'],
            tg_id=data['tg_id'],
            tg_nic=data['tg_nic']
        )

    async def get_comlink_player_data(self, data: json) -> ComlinkPlayerData:
        return ComlinkPlayerData(
            name=data['name'],
            level=data['level'],
            playerId=data['playerId'],
            lastActivityTime=data['lastActivityTime'],
            comlink_arena_rank=data['pvpProfile'][0]['rank'],
            comlink_fleet_arena_rank=data['pvpProfile'][1]['rank']
        )

    async def get_swgoh_guild_player_data(self, data: list[json]) -> list[SwgohGuildPlayerData]:
        return [
            SwgohGuildPlayerData(**player)
            for player in data
        ]

    async def get_member_contribution_list_data(self, contibution: list[dict]) -> list[MemberContribution]:
        result = [
            MemberContribution(
                currentValue=data['currentValue'],
                lifetimeValue=data['lifetimeValue'],
                type=data['type']
            )
            for data in contibution
        ]
        return result

    async def get_season_status_data(self, season: list[dict]) -> list[SeasonStatusData]:
        result = [
            SeasonStatusData(
                division=data['division'],
                endTime=data['endTime'],
                eventInstanceId=data['eventInstanceId'],
                joinTime=data['joinTime'],
                league=data['league'],
                losses=data['losses'],
                rank=data['rank'],
                remove=data['remove'],
                seasonId=data['seasonId'],
                seasonPoints=data['seasonPoints'],
                wins=data['wins']
            )
            for data in season
        ]
        return result

    async def get_comlink_guild_player_dict(self, raw_data: json) -> dict[ComlinkGuildPlayerData]:
        result = {player['playerName']: await self.get_comlink_guild_player_detail_data(player) for player in
                  raw_data['guild']['member']}
        return result

    async def get_comlink_guild_player_data(self, raw_data: json, player_name: str):
        for member in raw_data['guild']['member']:
            if member['playerName'] == player_name:
                return await self.get_comlink_guild_player_detail_data(member)

    async def get_comlink_guild_player_detail_data(self, data: json) -> ComlinkGuildPlayerData:
        player_data = ComlinkGuildPlayerData(
            characterGalacticPower=data['characterGalacticPower'],
            galacticPower=data['galacticPower'],
            guildJoinTime=data['guildJoinTime'],
            guildXp=data['guildXp'],
            lastActivityTime=data['lastActivityTime'],
            leagueId=data['leagueId'],
            lifetimeSeasonScore=data['lifetimeSeasonScore'],
            memberContribution=await self.get_member_contribution_list_data(data['memberContribution']),
            memberLevel=data['memberLevel'],
            playerId=data['playerId'],
            playerLevel=data['playerLevel'],
            playerName=data['playerName'],
            playerPortrait=data['playerPortrait'],
            playerTitle=data['playerTitle'],
            seasonStatus=await self.get_season_status_data(data['seasonStatus']),
            shipGalacticPower=data['shipGalacticPower'],
            squadPower=data['squadPower']
        )
        return player_data

    async def get_swgoh_player_detail_data(self, data: dict) -> PlayerDetailData:
        return PlayerDetailData(**data)
