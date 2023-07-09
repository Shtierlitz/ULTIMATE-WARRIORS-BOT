# src/errors.py

class Status404Error(Exception):
    pass


class DatabaseBuildError(Exception):
    """Raised when there is an error building the database"""
    pass


class AddIdsError(Exception):
    """Raised when there is an error building the database"""
    pass