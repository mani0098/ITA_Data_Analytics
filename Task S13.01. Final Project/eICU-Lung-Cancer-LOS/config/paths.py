"""
Project path definitions.

All filesystem paths used in the project are centralized here.

This module also creates the required directory structure automatically.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"

SRC_DIR = PROJECT_ROOT / "src"

SQL_DIR = PROJECT_ROOT / "sql"

NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"

OUTPUT_DIR = PROJECT_ROOT / "outputs"

SCHEMA_DIR = OUTPUT_DIR / "schema"

COHORT_DIR = OUTPUT_DIR / "cohort"

PROCESSED_DIR = OUTPUT_DIR / "processed"

REPORT_DIR = OUTPUT_DIR / "reports"

MODEL_DIR = OUTPUT_DIR / "models"

LOG_DIR = OUTPUT_DIR / "logs"

SQL_HISTORY_DIR = OUTPUT_DIR / "sql_history"

DATA_DIR = PROJECT_ROOT / "data"

DEMO_DATA_DIR = DATA_DIR / "demo"

FULL_DATA_DIR = DATA_DIR / "full"

SQL_SCHEMA_DIR = SQL_DIR / "schema"

SQL_COHORT_DIR = SQL_DIR / "cohort"

SQL_FEATURE_DIR = SQL_DIR / "features"

SQL_VALIDATION_DIR = SQL_DIR / "validation"

FIGURE_DIR = PROJECT_ROOT / "figures"

DOC_DIR = PROJECT_ROOT / "docs"

REFERENCE_DIR = PROJECT_ROOT / "references"

TEST_DIR = PROJECT_ROOT / "tests"

PRIVATE_DATA_DIR = PROJECT_ROOT / "private_data"

REDUCED_DATA_DIR = PRIVATE_DATA_DIR / "reduced"

DIRECTORIES = [
    DATA_DIR,
    DEMO_DATA_DIR,
    FULL_DATA_DIR,
    PRIVATE_DATA_DIR,
    REDUCED_DATA_DIR,
    OUTPUT_DIR,
    SCHEMA_DIR,
    COHORT_DIR,
    PROCESSED_DIR,
    REPORT_DIR,
    MODEL_DIR,
    LOG_DIR,
    SQL_HISTORY_DIR,
    SQL_SCHEMA_DIR,
    SQL_COHORT_DIR,
    SQL_FEATURE_DIR,
    SQL_VALIDATION_DIR,
    FIGURE_DIR,
    DOC_DIR,
    REFERENCE_DIR,
    TEST_DIR,
]


def create_project_structure() -> None:
    """
    Create all required project directories if they do not already exist.
    """

    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)

create_project_structure()