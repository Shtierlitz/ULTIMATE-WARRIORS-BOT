# apsched.py
import asyncio
import logging
import os

from create_bot import bot

from settings import async_session_maker
from src.guild import GuildData
from src.utils import get_new_day_start, send_points_message
from src.player import Player, PlayerData, PlayerScoreService, PlayerPowerService
from datetime import datetime, timedelta
from sqlalchemy import and_, select, cast, Integer


async def check_guild_points(*args, **kwargs):
    try:
        message_list_ru = [
            "ну камон. Сдай энку вовремя! У тебя",
            "Большой брат следит за твоей энкой. Офицеры уже оповещены, что у тебя всего",
            "I see you! You cannot hide. Сейчас",
            "ты знаешь? Это ж знатно надоедает. У тебя всего",
            "сдашь энку и у нас будут рейгды регулярные. Давай) У тебя уже",
            "не подводи остальных. Сдай энку. У тебя уже",
            "сдай энку. Подавай пример остальным. Не оказывайся в списке аутсайдеров. У тебя уже",
            "не втыч! Энка! Сейчас",
            "ЭНКАААААААА!!!!! Сейчас",
            "Не будешь сдавать энку вовремя, разработчик меня переделает так что срать спамом буду еще и на телефон)) Сдай энку. У тебя сейчас"
        ]
        message_list_eng = [
            "Comе on man! Hand over the reid points on time! You have",
            "Big brother is watching your reid points. The officers have already been notified that you have only,"
            "I see you! You cannot hide. Now",
            "You know? Well, it's notably annoying. You have "
            "pass the reid points and we'll have regular raids. Come on) You've got ",
            "Don't let the others down. Turn in the reid points. You already have",
            "Pass reid points. Set an example for others. Don't end up on the underdog list. You already have",
            "Don't stick! Reid points! Now",
            "Reeeeeeeid poooooiiiints!!!!! Now",
            "If you don't turn in the reid points on time, the developer will remake me so I'll also shit with spam on the phone)) Turn in the reid points. You have now"
        ]
        env_members = os.environ.get("ENG_MEMBERS")
        eng_members_list = list(map(int, env_members.split(",")))
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
            try:
                if player.tg_id != "null":
                    if player.ally_code in eng_members_list:
                        await send_points_message(player, message_list_eng, rus=False)
                    else:
                        await send_points_message(player, message_list_ru, rus=True)
                    await asyncio.sleep(10)
                else:
                    await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                                           f"У {player.name} нету идентификатора в боте.")
            except Exception as e:
                print(player.name, e)
                await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                                       f"Произошла ошибка при отправке автосообщения про энку: \n\n{e}\n\nПроизошло это на пользователе: {player.name}\nВероятнее всего не з\дал свой тг id или не нажал /start у бота")
        # Отправляем офицерам напоминалку кто не сдал еще энку
        message_strings = await PlayerScoreService.get_reid_lazy_fools()
        await bot.send_message(int(os.environ.get('OFFICER_CHAT_ID')), message_strings)
    except Exception as e:
        print(e)
        await bot.send_message(os.environ.get('OFFICER_CHAT_ID'),
                               f"Произошла ошибка при отправке автосообщения про энку: \n\n{e}\n.")


async def update_db(*args, **kwargs):
    await GuildData().build_db()
    await PlayerData().update_players_data()


async def final_points_per_month():
    # Check if today is the last day of the month
    tomorrow = datetime.now() + timedelta(days=1)
    logging.info(f"функция шедулера по отправки месячного сообщения выполнилась {tomorrow.day}")
    if tomorrow.day == 1:
        try:
            message = await PlayerScoreService.get_raid_scores_all()
            await bot.send_message(os.environ.get("POINTS_CHAT_ID"), message)
        except Exception as e:
            await bot.send_message(os.environ.get('POINTS_CHAT_ID'),
                                   f"Произошла ошибка при отправке месячного графика про энку:\n\n❌❌{e}❌❌\n\n")


async def final_gp_per_month():
    # Check if today is the last day of the month
    tomorrow = datetime.now() + timedelta(days=1)
    logging.info(f"функция шедулера по отправки месячного сообщения выполнилась {tomorrow.day}")
    if tomorrow.day == 1:
        try:
            message = await PlayerPowerService.get_galactic_power_all()
            await bot.send_message(os.environ.get("GP_CHAT_ID"), message)
        except Exception as e:
            await bot.send_message(os.environ.get('GP_CHAT_ID'),
                                   f"Произошла ошибка при отправке месячного графика про энку:\n\n❌❌{e}❌❌\n\n")
