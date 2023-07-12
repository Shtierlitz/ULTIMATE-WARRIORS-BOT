# handlers/admin.py
from aiogram import types, Dispatcher
import plotly.express as px
from plotly import graph_objs as go
from plotly import io as pio
from sqlalchemy import select

from create_bot import bot
import io
import json
import os

from db_models import Player
from src.utils import split_list
from settings import async_session_maker

COMMANDS = {
    "admin": "Получить информацию о доступных командах администратора",
    "add_player": "Записать нового игрока в базу (через пробел 3 значения - имя код_союзника тг_id)",
    "players_list": "Вывести все записи по игрокам (не стоит использовать в общих чатах)",
    "delete_player": "Удалить игрока из базы по имени",
    "grafic имя_игрока": "Выводит график сдачи игроком рейдовых купонов за все месяц"
    # Добавьте здесь другие команды по мере необходимости
}


async def admin_command_help(message: types.Message):
    """Выводит инфо о командах"""
    try:
        commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
        await bot.send_message(message.chat.id, f"Список доступных команд администратора:\n\n{commands}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def add_player(message: types.Message):
    """Добавляет игрока в ids.json"""
    try:
        player_info = message.text.split(" ")
        if len(player_info) != 5:
            await bot.send_message(message.chat.id,
                                   f"Неверный формат команды. Используйте: \n/add_player имя код_союзника тг_id тг_ник\n Все через один пробел.")
            return
        # имя игрока, код и ID телеграма и ник в телеграме
        player_name, ally_code, tg_id, tg_nic = player_info[1], player_info[2], player_info[3], player_info[4]

        file_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'ids.json')
        if os.path.exists(file_path):
            with open(file_path, "r") as json_file:
                data = json.load(json_file)
            if len(data) >= 50:
                await bot.send_message(message.chat.id, f"Превышено число членов гильдии. Добавление невозможно!")
            else:
                # Добавление нового игрока в список
                data.append({
                    ally_code: {
                        "player_name": player_name,
                        "tg_id": tg_id,
                        "tg_nic": tg_nic
                    }
                })

                # Запись обновленного списка в файл
                with open(file_path, "w") as json_file:
                    json.dump(data, json_file, ensure_ascii=False)

                await bot.send_message(message.chat.id, f"Игрок {player_name} был добавлен в список.")
        else:
            await bot.send_message(message.chat.id, "Файл ids.json не найден.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def players_list(message: types.Message):
    """Отправляет содержимое файла ids.json в чат"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'ids.json')
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as json_file:
                data = json.load(json_file)

            # Перебираем список игроков и формируем строку
            msg_list = []
            for index, player in enumerate(data):
                for ally_code, info in player.items():
                    msg = (
                        f"{index+1}: {info['player_name']}\n"
                        f"Код союзника: {ally_code}\n"
                        f"ID: {info['tg_id']}\n"
                        f"TG_NIC: {info['tg_nic']}\n"
                        f"{'-' * 30}\n"
                    )
                    msg_list.append(msg)
            msg_list.append(f"Всего: {len(data)}")
            final_lst_1, final_lst_2 = split_list(msg_list, 2)     # hfpltkztv
            # Соединяем все сообщения в одну большую строку
            final_msg_1 = ''.join(final_lst_1)
            final_msg_2 = ''.join(final_lst_2)

            await bot.send_message(message.chat.id, final_msg_1)
            await bot.send_message(message.chat.id, final_msg_2)
        else:
            await bot.send_message(message.chat.id, "Файл ids.json не найден.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def delete_player(message: types.Message):
    """Удаляет игрока из JSON файла"""
    try:
        player_name = message.get_args()  # Получаем имя игрока
        if not player_name:
            await message.reply("Пожалуйста, предоставьте имя игрока.")
            return

        file_path = os.path.join(os.path.dirname(__file__), '../api/ids.json')

        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        player_found = False  # флаг, чтобы отслеживать, найден ли игрок

        for index, player in enumerate(data):
            for ally_code, info in player.items():
                if info["player_name"] == player_name:
                    del data[index]  # Удаляем запись игрока
                    player_found = True  # отмечаем, что игрок найден
                    break

            if player_found:
                break
        else:
            await message.reply("Игрок с таким именем не найден.")
            return

        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=2)

        await bot.send_message(message.chat.id, f"Игрок {player_name} удален из списка.")

    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


async def send_month_player_grafic(message: types.Message):
    """Отправляет график рейда игрока"""
    # try:
    player_name = message.get_args()
    if not player_name:
        await message.reply(f"Неверный формат ввода. Правильно:\n/grafic имя_игрока\nЧерез пробел.")
        return

    # Извлечение данных из базы данных
    async with async_session_maker() as session:
        # player_data = session.query(Player).filter_by(name=player_name).all()
        query = await session.execute(
            select(Player).filter_by(name=player_name))
        player_data = query.scalars().all()

    # Проверка, есть ли данные
    if not player_data:
        await message.reply(f"Неверно введено имя \"{player_name}\". Попробуйте проверить правильность написания")
        return

    # Подготовка данных для построения графика
    update_times = [player.update_time for player in player_data]
    reid_points = [player.reid_points for player in player_data]

    # Построение графика
    fig = go.Figure(data=go.Scatter(
        x=update_times,
        y=reid_points,
        mode='lines+markers+text',
        text=reid_points,
        textposition='top center'))

    fig.update_layout(
        title=f'Reid Points Over Month for {player_name}',
        xaxis_title='Update Time',
        yaxis_title='Reid Points',
        yaxis=dict(
            range=[-100, 700],
            tickmode='linear',
            tick0=0,
            dtick=50
        )
    )

    # Сохранение графика в виде файла изображения
    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png')
    buf.seek(0)

    await bot.send_photo(chat_id=message.chat.id, photo=buf)
    # except Exception as e:
    #     await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")

async def send_month_total_grafic(message: types.Message):
    """Отправляет график рейда для всех игроков"""
    try:
        # Извлечение данных из базы данных
        async with async_session_maker() as session:
            all_players = session.query(Player).all()
        players_data = {}

        for player in all_players:
            if player.name not in players_data:
                players_data[player.name] = {'update_times': [], 'reid_points': []}

            players_data[player.name]['update_times'].append(player.update_time)
            players_data[player.name]['reid_points'].append(player.reid_points)

        # Подготовка данных для построения графика
        fig = go.Figure(layout=go.Layout(
            autosize=False,
            width=2000,  # Укажите ширину в пикселях
            height=1200)  # Укажите высоту в пикселях
        )

        color_palette = px.colors.qualitative.Safe

        for idx, (player_name, data) in enumerate(players_data.items()):
            fig.add_trace(go.Scatter(
                x=data['update_times'],
                y=data['reid_points'],
                mode='lines+markers+text',
                text=data['reid_points'],
                textposition='top center',
                name=player_name,
                line=dict(color=color_palette[idx % len(color_palette)], width=2),  # Устанавливаем толщину линии
                marker=dict(size=10)  # Устанавливаем размер точки
            ))

        fig.update_layout(
            title=f'Reid Points Over Month for All Players',
            xaxis_title='Update Time',
            yaxis_title='Reid Points',
            yaxis=dict(
                range=[-100, 700],
                tickmode='linear',
                tick0=0,
                dtick=50
            )
        )

        # Сохранение графика в виде файла изображения
        buf = io.BytesIO()
        pio.write_image(fig, buf, format='png')
        buf.seek(0)

        await bot.send_photo(chat_id=message.chat.id, photo=buf)
    except Exception as e:
        await message.reply(f"Ошибка: {e}.\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar")


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(add_player, commands=['add_player'], is_chat_admin=True)
    dp.register_message_handler(players_list, commands=['players_list'], is_chat_admin=True)
    dp.register_message_handler(delete_player, commands=['delete_player'], is_chat_admin=True)
    dp.register_message_handler(admin_command_help, commands=['admin'], is_chat_admin=True)
    dp.register_message_handler(send_month_player_grafic, commands=['grafic'], is_chat_admin=True)
    dp.register_message_handler(send_month_total_grafic, commands=['grafic_all'], is_chat_admin=True)
