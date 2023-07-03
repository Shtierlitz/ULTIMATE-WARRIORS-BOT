# api/guild_parser.py

import requests
import json


def show_guild_members(request: requests):
    print("request status code ==", request)

    if request.status_code == 200:
        data = request.json()
        # print(data['data']['members'])
        for i in data['data']['members']:
            # print(i['player_name'], i['league_name'], i['ally_code'])
            print(i.keys())


link = 'http://api.swgoh.gg/'

my_ally_code = '796483269'
guild_id = '0rNNFa76RXyv0C3suyUkFA'
guild_url = "/g/0rNNFa76RXyv0C3suyUkFA/"

guild_profile = requests.get("http://api.swgoh.gg/guild-profile/0rNNFa76RXyv0C3suyUkFA")

show_guild_members(guild_profile)

def show_player_data(request:requests):
    if request.status_code == 200:
        data = request.json()
        # print(data['data'].items())
        for i in data['data'].items():
            print(i)


player_search = requests.get(f'http://api.swgoh.gg/player/{my_ally_code}/')
# show_player_data(player_search)