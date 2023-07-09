# prod_settings.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Создание базового класса модели
Base = declarative_base()

# Создание движка SQLAlchemy для взаимодействия с базой данных PostgreSQL
engine = create_engine('postgresql://user:password@localhost/guild_db')

# Создание всех таблиц в базе данных
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

