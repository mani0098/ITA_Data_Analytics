"""
Custom exceptions used throughout the project.

Author
------
Mani Rezaeirad

Project
-------
Early Prediction of Prolonged ICU Stay in Lung Cancer Patients
"""


class EICUProjectError(Exception):
    """
    Base exception for the entire project.
    """

    pass


class DatabaseConnectionError(EICUProjectError):
    """
    Raised when the connection to the database cannot be established.
    """

    pass


class DatabaseNotConnectedError(EICUProjectError):
    """
    Raised when attempting to execute queries before connecting.
    """

    pass


class QueryExecutionError(EICUProjectError):
    """
    Raised when an SQL query fails.
    """

    pass


class TableNotFoundError(EICUProjectError):
    """
    Raised when the requested table does not exist.
    """

    pass


class InvalidTableError(EICUProjectError):
    """
    Raised when an invalid table name is provided.
    """

    pass


class SchemaValidationError(EICUProjectError):
    """
    Raised when schema validation fails.
    """

    pass


class ConfigurationError(EICUProjectError):
    """
    Raised when the configuration is invalid.
    """

    pass