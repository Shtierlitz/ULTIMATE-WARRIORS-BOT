# prod_settings.py

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Создание базового класса модели
Base = declarative_base()

# Создание движка SQLAlchemy для взаимодействия с базой данных PostgreSQL
engine = create_async_engine(
    f'postgresql+asyncpg://{os.environ.get("DB_USER")}:{os.environ.get("DB_PASS")}@host.docker.internal/{os.environ.get("DB_NAME")}')

# Создание всех таблиц в базе данных
# Обратите внимание, что операция создания всех таблиц в базе данных должна быть обернута в асинхронную функцию
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Создание фабричной функции для создания новых асинхронных сессий
async_session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession, future=True)

# Создаем обработчик файлов с mode='w', чтобы файл был перезаписан при каждом запуске
file_handler = logging.FileHandler('my_log_file.log', mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)  # или любой уровень, который вы хотите

# Создаем обработчик потока (консоли)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)  # или любой уровень, который вы хотите

# Создаем форматтер и добавляем его в обработчики
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Создаем и настраиваем логгер
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # или любой уровень, который вы хотите

# Добавляем обработчики в логгер
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Используем
logger.debug('This message should go to the log file and console')

# Настраиваем базовую конфигурацию логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[stream_handler, file_handler])
