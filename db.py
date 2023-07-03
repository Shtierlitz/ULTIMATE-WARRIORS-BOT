# db.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Создание базового класса модели
Base = declarative_base()

# ('guild_contribution', 1581367)

# Создание движка SQLAlchemy для взаимодействия с базой данных
engine = create_engine('sqlite:///guild.db')
from db_models import Player
# Создание всех таблиц в базе данных
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)



