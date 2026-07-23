"""
Database access layer for the eICU project.

This module provides the EICUDatabase class, which is the single entry point
for all interactions with the eICU MySQL database.

Author
------
Mani Rezaeirad

Project
-------
Early Prediction of Prolonged ICU Stay in Lung Cancer Patients
"""

from __future__ import annotations

from functools import lru_cache
from time import perf_counter
from typing import Optional

import pandas as pd

from sqlalchemy import URL, create_engine
from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.engine import Inspector

from pathlib import Path

import os

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from config.paths import SQL_HISTORY_DIR

from config.paths import PROJECT_ROOT

from config.config import load_config

from src.logger import get_logger

from src.exceptions import (
    DatabaseConnectionError,
    DatabaseNotConnectedError,
    QueryExecutionError
)

class EICUDatabase:
    """
    High-level interface for interacting with the eICU database.

    Notes
    -----
    Every notebook should instantiate exactly one object of this class.

    Example
    -------
    >>> db = EICUDatabase()
    >>> db.connect()
    >>> tables = db.tables()
    >>> db.disconnect()
    """

    def __init__(self) -> None:
        """
        Initialize the database object.

        No database connection is established here.
        """

        self.config = load_config()

        self.logger = get_logger(__name__)

        self.engine: Optional[Engine] = None

        self.inspector: Optional[Inspector] = None

        self.logger.info("EICUDatabase initialized.")

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """
        Return whether the database is connected.

        Returns
        -------
        bool
        """

        return self.engine is not None

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    def connect(self) -> None:
        """
        Establish a connection to the database.

        Raises
        ------
        DatabaseConnectionError
        """

        if self.connected:

            self.logger.info("Already connected.")

            return

        cfg = self.config.database

        url = (
            f"mysql+pymysql://"
            f"{cfg.username}:{cfg.password}"
            f"@{cfg.host}:{cfg.port}"
            f"/{cfg.database}"
        )

        self.logger.info("Connecting to database...")

        start = perf_counter()

        try:

            self.engine = create_engine(
                url,
                pool_pre_ping=True,
                future=True,
            )

            self.inspector = inspect(self.engine)

        except Exception as exc:

            raise DatabaseConnectionError(
                f"Unable to connect to database.\n{exc}"
            ) from exc

        elapsed = perf_counter() - start

        self.logger.info(
            "Connected successfully (%.2f s).",
            elapsed,
        )

    def disconnect(self) -> None:
        """
        Close the database connection.
        """

        if not self.connected:

            return

        self.engine.dispose()

        self.engine = None

        self.inspector = None

        self.logger.info("Database disconnected.")

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def _ensure_connection(self) -> None:
        """
        Ensure an active connection exists.

        Raises
        ------
        DatabaseNotConnectedError
        """

        if not self.connected:

            raise DatabaseNotConnectedError(
                "Database connection has not been established."
            )

   
    def _log_query(
        self,
        sql: str,
        elapsed: float,
        rows: int,
    ) -> None:
        """
        Log SQL execution information.

        Parameters
        ----------
        sql
            Executed SQL query.

        elapsed
            Execution time in seconds.

        rows
            Number of returned rows.
        """

        self.logger.info(
            "Query executed | Rows=%d | Time=%.3f s",
            rows,
            elapsed,
        )

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        filename = SQL_HISTORY_DIR / f"{timestamp}.sql"

        with open(filename, "w", encoding="utf-8") as file:

            file.write(sql)

 
    def query(
        self,
        sql: str,
    ) -> pd.DataFrame:
        """
        Execute an SQL query.

        Parameters
        ----------
        sql
            SQL statement.

        Returns
        -------
        pandas.DataFrame
        """

        self._ensure_connection()

        start = perf_counter()

        try:

            dataframe = pd.read_sql(
                text(sql),
                self.engine,
            )

        except Exception as exc:

            raise QueryExecutionError(
                f"SQL execution failed.\n{exc}"
            ) from exc

        elapsed = perf_counter() - start

        memory = dataframe.memory_usage(
            deep=True
        ).sum() / 1024 ** 2

        self.logger.info(
            (
                "Rows=%d | "
                "Columns=%d | "
                "Memory=%.2f MB | "
                "Time=%.3f s"
            ),
            len(dataframe),
            len(dataframe.columns),
            memory,
            elapsed,
        )

        self._log_query(
            sql,
            elapsed,
            len(dataframe),
        )

        return dataframe
    

    def preview(
        self,
        table: str,
        limit: int = 5,
    ) -> pd.DataFrame:
        """
        Preview a table.

        Parameters
        ----------
        table
            Table name.

        limit
            Number of rows.

        Returns
        -------
        pandas.DataFrame
        """

        sql = f"""
        SELECT *
        FROM {table}
        LIMIT {limit}
        """

        return self.query(sql)
    

    def count(
        self,
        table: str,
    ) -> int:
        """
        Return the number of rows in a table.
        """

        sql = f"""
        SELECT COUNT(*) AS n
        FROM {table}
        """

        dataframe = self.query(sql)

        return int(dataframe.iloc[0, 0])
    


    @lru_cache(maxsize=1)
    def get_engine() -> Engine:
        """
        Create and cache one reusable SQLAlchemy engine.
        """

    required_variables = (
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
    )

    missing = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing:
        raise EnvironmentError(
            "Missing database environment variables: "
            + ", ".join(missing)
        )

    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True,
    )