# database/config.py
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    dialect: str = "postgresql"
    database: str = "steam_pars"
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: Optional[str] = None
    pool_size: int = 20
    max_overflow: int = 10
    echo: bool = False

    @property
    def connection_string(self) -> str:
        """Возвращает строку подключения к базе данных"""
        if self.dialect == "sqlite":
            return f"sqlite:///{self.database}"
        elif self.dialect == "postgresql":
            # Формат: postgresql://username:password@host:port/database
            auth = f"{self.username}:{self.password}@" if self.password else f"{self.username}@"
            return f"postgresql://{auth}{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported dialect: {self.dialect}")


def get_database_config() -> DatabaseConfig:
    """Получает конфигурацию базы данных из переменных окружения"""
    return DatabaseConfig(
        dialect=os.getenv("DB_DIALECT", "postgresql"),
        database=os.getenv("DB_NAME", "steam_pars"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        username=os.getenv("DB_USERNAME", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        echo=os.getenv("DB_ECHO", "false").lower() == "true"
    )