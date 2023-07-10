# apsched.py
import asyncio
import os

from create_bot import bot
from create_bot import session
from handlers.member import handle_exception
from src.guild import GuildData
from src.utils import get_new_day_start
from src.player import Player, PlayerData

from sqlalchemy import and_
from dotenv import load_dotenv
import random as rn

load_dotenv()



async def check_guild_points(*args, **kwargs):
    message_list = [
        "ну камон. Сдай энку вовремя! У тебя",
        "Большой брат следит за твоей энкой. Офицеры уже оповещены, что у тебя всего",
        "I see you! You cannot hide. Не хватает",
        "ты знаешь? Это ж знатно надоедает. У тебя всего",
        "сдашь энку и у нас будут рейгды регулярные. Давай) У тебя уже",
        "не подводи остальных. Сдай энку. У тебя уже",
        "сдай энку. Подавай пример остальным. Не оказывайся в списке аутсайдеров. У тебя уже",
        "не втыч! Энка! Всего",
        "ЭНКАААААААА!!!!! Всего",
        "Не будешь сдавать энку вовремя, разработчик меня переделает так что срать спамом буду еще и на телефон)) Сдай энку. У тебя сейчас"
    ]
    new_day_start = get_new_day_start()

    existing_user_today = session.query(Player).filter(
        and_(
            Player.update_time >= new_day_start,
            Player.tg_id != 'null',
            Player.reid_points < 600
        )
    ).all()
    len(existing_user_today)
    officer_id_list_str = os.environ.get('ADMIN_LIST_STR')
    officer_id_list = officer_id_list_str.split(',')
    for player in existing_user_today:
        await bot.send_message(player.tg_id, f"{player.name}, {rn.choice(message_list)} {player.reid_points} купонов.")
        for ID in officer_id_list:
            await bot.send_message(ID, f"{player.name} не сдал вс. энку {player.reid_points}")


async def update_db(*args, **kwargs):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, PlayerData().update_players_data)
    future.add_done_callback(handle_exception)
    future2 = loop.run_in_executor(None, GuildData().build_db)
    future2.add_done_callback(handle_exception)


async def send_message_interval(*args, **kwargs):
    await bot.send_message(562272797, "С интервалом 1 min")
