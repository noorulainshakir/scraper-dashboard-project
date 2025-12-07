"""
Custom exceptions
"""


class AppException(Exception):
    """Base application exception"""
    pass


class JobNotFoundError(AppException):
    """Job not found exception"""
    pass


class JobAlreadyRunningError(AppException):
    """Job is already running"""
    pass


class JobNotRunningError(AppException):
    """Job is not currently running"""
    pass


class ScheduleNotFoundError(AppException):
    """Schedule not found exception"""
    pass


class ConfigurationError(AppException):
    """Configuration error"""
    pass

