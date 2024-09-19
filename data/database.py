# Database using sqlalchemy extension
import asyncio
import os

import asyncpg
import psycopg2
from sqlalchemy import text, create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from data.models.base_model import Base
from data.models import event, member, nickname, base_model

class OptionalError:
    pass

class Database:
    def __init__(self, db_config):
        self.name = db_config["name"]
        self.config = db_config
        self.connection_string = \
            f'postgresql+psycopg2://{os.getenv("PGUSER")}:{os.getenv("PGPASSWORD")}@{os.getenv("PGHOST")}:{os.getenv("PGPORT")}/{os.getenv("PG_DATABASE")}'
        print(self.connection_string)
        self.sync_engine = create_engine(self.connection_string)
        self.async_engine = None
        self.async_session = None
        # Создаем фабрику сессий для асинхронной работы с базой данных


    async def get_session(self) -> AsyncSession:
        """
        Получить асинхронную сессию для работы с базой данных.
        Возвращает объект AsyncSession.

        :return: асинхронная сессия базы данных.
        """
        async with self.async_session() as session:
            yield session

    def get_session_sync(self) -> AsyncSession:
        return self.async_session()



    # def is_db_exist(self):
    #     exists = False
    #     try:
    #         with self.sync_engine.connect() as conn:
    #             query = text("SELECT 1 FROM pg_database WHERE datname = :db_name")
    #             result = conn.execute(query, {'db_name': self.name})
    #             exists = result.scalar() is not None
    #     except SQLAlchemyError:
    #         exists = False
    #     return exists

    def init_db(self):
        # if not self.is_db_exist():
        #     with self.sync_engine.connect() as conn:
        #         try:
        #             conn.execute(text("COMMIT"))  # Ensure there are no open transactions
        #             conn.execute(text(f"CREATE DATABASE {self.name}"))
        #             print(f"База данных {self.name} создана")
        #         except SQLAlchemyError as e:
        #             conn.execute(text("ROLLBACK"))
        #             print(f"Произошла ошибка во время создания базы данных: {e}")
        #
        #     # Обновляем строку подключения для работы с новой базой данных
        #     self.connection_string = \
        #         f'postgresql+psycopg2://{os.getenv("PGUSER")}:{os.getenv("PGPASSWORD")}@{os.getenv("PGHOST")}:{os.getenv("PGPORT")}/{os.getenv("PG_DATABASE")}'
        #     self.sync_engine = create_engine(self.connection_string, echo=True)

        # Используем синхронный контекст для создания таблиц
        try:
            # Создаем таблицы
            Base.metadata.create_all(self.sync_engine)
            print("Таблицы инициализированы")
        except SQLAlchemyError as e:
            print(f"Произошла ошибка при инициализации базы данных: {e}")
        self.connection_string = f'postgresql+asyncpg://{os.getenv("PGUSER")}:{os.getenv("PGPASSWORD")}@{os.getenv("PGHOST")}:{os.getenv("PGPORT")}/{os.getenv("PG_DATABASE")}'
        print(self.connection_string)
        self.async_engine = create_async_engine(self.connection_string)
        self.async_session = sessionmaker(
            bind=self.async_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
