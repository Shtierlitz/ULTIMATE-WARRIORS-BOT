# apsched.py
import asyncio
import os

from create_bot import bot
# from create_bot import session
from handlers.member import handle_exception
from settings import async_session_maker
from src.guild import GuildData
from src.utils import get_new_day_start
from src.player import Player, PlayerData, PlayerScoreService
from aiogram.utils.exceptions import ChatNotFound

from sqlalchemy import and_, select, cast, Integer
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
        "не втыч! Энка! Сейчас",
        "ЭНКАААААААА!!!!! Сейчас",
        "Не будешь сдавать энку вовремя, разработчик меня переделает так что срать спамом буду еще и на телефон)) Сдай энку. У тебя сейчас"
    ]
    new_day_start = get_new_day_start()

    async with async_session_maker() as session:
        result = await session.execute(
            select(Player).where(
                and_(
                    Player.update_time >= new_day_start,
                    Player.tg_id != 'null',
                    cast(Player.reid_points, Integer) < 600
                )
            )
        )
        existing_user_today = result.scalars().all()

    print(len(existing_user_today))
    for player in existing_user_today:
        if player.tg_id != "null":
            try:
                await bot.send_message(player.tg_id, f"{player.name}, {rn.choice(message_list)} {player.reid_points} купонов.")
            except ChatNotFound as e:
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), f"У {player.name} не подключена телега к чату.")
        else:
            await bot.send_message(os.environ.get('OFFICER_CHAT_ID'), f"У {player.name} нету идентификатора в боте.")
    # Отправляем офицерам напоминалку кто не сдал еще энку
    message_strings = await PlayerScoreService.get_reid_lazy_fools()
    await bot.send_message(int(os.environ.get('OFFICER_CHAT_ID')), message_strings)



async def update_db(*args, **kwargs):
    await PlayerData().update_players_data()
    await GuildData().build_db()


async def send_message_interval(*args, **kwargs):
    await bot.send_message(562272797, "С интервалом 1 min")
