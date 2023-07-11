# settings.py

import os
import cloudinary

try:
    from local_settings import *
except ImportError:
    from prod_settings import *

# Теперь, когда Base определен, вы можете импортировать Player
from db_models import Player

# # Добавить таблицу в базу данных
# Base.metadata.create_all(engine)

# Создание всех таблиц в базе данных
# Обратите внимание, что операция создания всех таблиц в базе данных должна быть обернута в асинхронную функцию
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET")
    )