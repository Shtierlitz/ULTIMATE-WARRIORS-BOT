# handlers/send_group_message.py

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import session, bot
from src.player import Player
from src.utils import get_new_day_start


class Form(StatesGroup):
    users = State()
    message = State()


async def start_group_command(message: types.Message):
    await message.answer("Введите никнеймы всех кому вы хотите отправить сообщение через пробел.")
    await Form.users.set()


async def process_users(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # Заменяем символ "@" на пустую строку перед разделением имен пользователей
        data['users'] = message.text.replace("@", "").split(" ")
    await message.answer("Введите сообщение, которое хотите отправить.")
    await Form.next()



async def process_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text  # Сохраняем текст сообщения

        new_day_start = get_new_day_start()

        all_users = session.query(Player.tg_nic, Player.tg_id).filter(
                    Player.update_time >= new_day_start
                ).all()
        print(data['users'])
        users_from_db = {user for user in all_users if user.tg_nic in data['users']}
        print(users_from_db)

        failed_users = []  # Список пользователей, которым не удалось отправить сообщение

        if users_from_db:
            # Отправляем сообщение каждому пользователю
            for user in users_from_db:
                print(user)
                try:
                    await bot.send_message(user[1], data['message'])
                except Exception as e:
                    failed_users.append(user[0])  # Добавляем пользователя в список неудач
                    print(f"Не удалось отправить сообщение пользователю {user[0]}: {e}")

        if failed_users:
            await message.answer("Не удалось отправить сообщения следующим пользователям: " + ", ".join(failed_users))
        else:
            await message.answer("Сообщения были отправлены.")

    await state.finish()




def register_handlers_group_message(dp: Dispatcher):
    dp.register_message_handler(start_group_command, commands='group', is_chat_admin=True)
    dp.register_message_handler(process_users, state=Form.users, is_chat_admin=True)
    dp.register_message_handler(process_message, state=Form.message, is_chat_admin=True)
