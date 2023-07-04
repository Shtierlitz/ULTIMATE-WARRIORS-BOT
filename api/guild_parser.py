# api/guild_parser.py
import os

import requests
import json


def show_guild_members(request: requests):
    print("request status code ==", request)

    if request.status_code == 200:
        data = request.json()
        # print(data['data']['members'])
        print(data['data'])
        # for i in data['data']:
        #     # print(i['player_name'], i['league_name'], i['ally_code'])
        #     print(i)


link = 'http://api.swgoh.gg/'

my_ally_code = '796483269'
guild_id = '0rNNFa76RXyv0C3suyUkFA'
guild_url = "/g/0rNNFa76RXyv0C3suyUkFA/"

guild_profile = requests.get("http://api.swgoh.gg/guild-profile/0rNNFa76RXyv0C3suyUkFA")


show_guild_members(guild_profile)

def show_player_data(request: requests):
    if request.status_code == 200:
        data = request.json()
        # print(data['data'].items())
        for i in data['data'].items():
            print(i)


player_search = requests.get(f'http://api.swgoh.gg/player/{my_ally_code}/')


# show_player_data(player_search)


# sync = requests.post(
#     f'http://api.swgoh.gg/players/{my_ally_code}/trigger-sync/',
#     auth=(os.environ.get("USER_NAME"), os.environ.get("USER_PASSWORD"))
# )
# sync_player(sync)


def make_json_ids():
    ar = []

    with open('ids.txt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()  # Удалить пробельные символы в начале и конце строки
            if line:  # Если строка не пустая
                key, value = line.split(': ')  # Разделить строку по ': '
                ar.append({key: value})  # Добавить словарь в список

    with open('ids.json', 'w', encoding='utf-8') as e:
        json.dump(ar, e, indent=4, ensure_ascii=False)


# make_json_ids()
