# create_bot.py

import os

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from dotenv import load_dotenv

import settings

load_dotenv()
storage = MemoryStorage()  # хранилище блока состояния

bot = Bot(token=os.environ.get('TOKEN'))  # читаем токен
dp = Dispatcher(bot, storage=storage)
session = settings.Session()
