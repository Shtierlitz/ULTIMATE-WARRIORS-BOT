# tests/test_handlers/test_start.py
import os

import pytest

from handlers.member import command_start, COMMANDS, command_gac_statistic
from unittest.mock import AsyncMock, call
from dotenv import load_dotenv
from pathlib import Path

# Получить путь к текущему файлу
current_file_path = os.path.realpath(__file__)
# Получить путь к каталогу текущего файла
current_dir_path = os.path.dirname(current_file_path)
# Сформировать путь к .env
env_file_path = os.path.join(current_dir_path, '..', '..', '.env')

dotenv_path = Path(env_file_path)

load_dotenv(dotenv_path=dotenv_path.resolve())


@pytest.mark.asyncio
async def test_start_behavior():
    bot = AsyncMock()
    message = AsyncMock()
    message.conf = {"is_guild_member": True}
    message.chat.id = os.environ.get('MY_ID')
    command_start.__globals__["bot"] = bot
    await command_start(message)
    commands = "\n".join([f"/{command} - {description}" for command, description in COMMANDS.items()])
    # print(bot.send_message.call_args_list)
    bot.send_message.assert_has_calls([
        call(message.chat.id, "Начинаем работу."),
        call(message.chat.id, f"Список доступных команд:\n\n{commands}")
    ], any_order=True)


@pytest.mark.asyncio
async def test_start_throws_exception():
    # Создаем экземпляр бота, который будет вызывать исключение при вызове `send_message`
    bot = AsyncMock()
    bot.send_message.side_effect = Exception("Test exception")

    message = AsyncMock()
    message.conf = {"is_guild_member": True}
    message.chat.id = os.environ.get('MY_ID')
    message.reply = AsyncMock()

    # Заменяем bot внутри функции на нашу подделку
    command_start.__globals__["bot"] = bot

    # Вызываем функцию
    await command_start(message)

    # Проверяем вызовы
    message.reply.assert_called_once_with(
        "Ошибка:\n\n❌❌Test exception❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar"
    )


@pytest.mark.asyncio
async def test_gac_statistic():
    # Создаем экземпляр бота
    bot = AsyncMock()

    # Создаем сообщение
    message = AsyncMock()
    message.conf = {"is_guild_member": True}
    message.chat.id = os.environ.get('MY_ID')
    message.reply = AsyncMock()

    # Заменяем bot внутри функции на нашу подделку
    command_gac_statistic.__globals__["bot"] = bot

    # Мокаем функцию gac_statistic
    gac_statistic_mock = AsyncMock(return_value=("stat1", "stat2", "stat3", "stat4", "stat5"))
    command_gac_statistic.__globals__["gac_statistic"] = gac_statistic_mock

    # Вызываем функцию
    await command_gac_statistic(message)

    # Проверяем вызовы
    message.reply.assert_called_once_with("Добываю статистику. Ожидайте выполнения...")
    bot.send_message.assert_has_calls([
        call(message.chat.id, text="stat1", parse_mode="Markdown"),
        call(message.chat.id, text="stat2", parse_mode="Markdown"),
        call(message.chat.id, text="stat3", parse_mode="Markdown"),
        call(message.chat.id, text="stat4", parse_mode="Markdown"),
        call(message.chat.id, text="stat5", parse_mode="Markdown"),
    ], any_order=False)  # порядок важен


@pytest.mark.asyncio
async def test_gac_statistic_throws_exception():
    # Создаем экземпляр бота, который будет вызывать исключение при вызове `send_message`
    bot = AsyncMock()
    bot.send_message.side_effect = Exception("Test exception")

    message = AsyncMock()
    message.conf = {"is_guild_member": True}
    message.chat.id = os.environ.get('MY_ID')
    message.reply = AsyncMock()

    # Заменяем bot внутри функции на нашу подделку
    command_start.__globals__["bot"] = bot

    # Вызываем функцию
    await command_start(message)

    # Проверяем вызовы
    message.reply.assert_called_once_with(
        "Ошибка:\n\n❌❌Test exception❌❌\n\nОбратитесь разработчику бота в личку:\nhttps://t.me/rollbar"
    )
