# settings.py

import os
import cloudinary

try:
    from local_settings import *
except ImportError:
    from prod_settings import *

# Теперь, когда Base определен, вы можете импортировать Player
from db_models import Player

# Добавить таблицу в базу данных
Base.metadata.create_all(engine)

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET")
    )