"""
Project configuration.

Database credentials are loaded from environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class DatabaseConfig:
    """
    Database connection parameters.
    """

    host: str
    port: int
    username: str
    password: str
    database: str


@dataclass(slots=True)
class ProjectConfig:
    """
    Global project configuration.
    """

    database: DatabaseConfig


def load_config() -> ProjectConfig:
    """
    Load project configuration from environment variables.

    Returns
    -------
    ProjectConfig
        Fully populated project configuration.
    """

    db = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        username=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_DATABASE", ""),
    )

    return ProjectConfig(database=db)