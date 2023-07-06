# api/guild_parser.py
import os
import time
from datetime import datetime

import requests
import json

from sqlalchemy import func

from create_bot import session
from db_models import Player


def some_func():
    current_date = datetime.now().date()
    players_list = session.query(Player).filter(func.date(Player.update_time) == current_date)
    result = []
    count_true = 0
    count_false = 0
    link_pre = 'https://swgoh.gg/p/'
    for i in players_list:
        request = requests.get(f"http://api.swgoh.gg/player/{i.ally_code}/gac-bracket/")
        # print(request.status_code)
        if request.status_code == 200:
            data = request.json()
            # result[i.name] = "зареган"
            print(i.name, "зареган", data)
            # message = f"{i.name} зареган. Противники: \n"
            # bracket_players = data['data']['bracket_players']
            # temp_list = []
            # for i in bracket_players:
            #     st = f"<a href=\"{link_pre}{i['ally_code']}\"{i['player_name']}</a>"
            #     temp_list.append(st)
            # message += ", ".join(temp_list)
            # result.append(message)
            # count_true += 1
        else:
            # result.append(f'{i.name} не зареган')
            print(i.name, "не зареган")
            # count_false += 1
    # result.append(f"Зареганных всего: {count_true}")
    # result.append(f"Завтыкали: {count_false}")

    return "\n".join(result)



            # success += 1
    #     else:
    #         fail += 1
    # print(success)
    # print(fail)


# some_func()


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


# show_guild_members(guild_profile)

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

