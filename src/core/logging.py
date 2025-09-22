import logging
import logging.config
import sys
import structlog

from src.core.config import settings


def get_log_level() -> int:
    """Convert string log level to logging constant."""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(settings.LOG_LEVEL.upper(), logging.INFO)


def configure_structlog() -> None:
    """Configure structlog with consistent formatting."""

    def add_log_level_upper(logger, method_name, event_dict):
        """Add log level in uppercase to match FastAPI format."""
        # Get the actual log level from the method name
        level_map = {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARNING",
            "error": "ERROR",
            "critical": "CRITICAL",
        }
        event_dict["level"] = level_map.get(method_name, "INFO")
        return event_dict

    def format_timestamp_no_microseconds(logger, method_name, event_dict):
        """Format timestamp without microseconds to match FastAPI format."""
        if "timestamp" in event_dict:
            # Remove microseconds from ISO timestamp
            timestamp = event_dict["timestamp"]
            if "." in timestamp:
                timestamp = timestamp.split(".")[0] + "Z"
            event_dict["timestamp"] = timestamp
        return event_dict

    processors = [
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # Force UTC timestamps
        format_timestamp_no_microseconds,  # Remove microseconds
        add_log_level_upper,  # Custom processor for uppercase levels
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_FORMAT.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Custom console renderer to match FastAPI's exact format
        def custom_console_renderer(logger, method_name, event_dict):
            """Custom console renderer that matches FastAPI's exact format."""
            timestamp = event_dict.get("timestamp", "")
            level = event_dict.get("level", "INFO")
            message = event_dict.get("event", "")

            # Format to match FastAPI: timestampZ [LEVEL    ] message
            formatted = f"{timestamp} [{level:<7}] {message}"

            # Add any additional context
            context = {
                k: v
                for k, v in event_dict.items()
                if k not in ["timestamp", "level", "event"]
            }
            if context:
                context_str = " ".join(f"{k}={v}" for k, v in context.items())
                formatted += f" {context_str}"

            return formatted

        processors.append(custom_console_renderer)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(get_log_level()),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def configure_standard_logging() -> None:
    """Configure standard Python logging to be consistent with structlog."""
    import logging.handlers
    from datetime import datetime, timezone

    class UTCFormatter(logging.Formatter):
        """Custom formatter that converts timestamps to UTC with no microseconds."""

        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            if datefmt:
                return dt.strftime(datefmt)
            # Format without microseconds to match FastAPI format
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    log_format = "%(asctime)sZ [%(levelname)-7s] %(message)s"

    if settings.LOG_FORMAT.lower() == "json":
        log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": UTCFormatter,
                    "format": log_format,
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                },
                "uvicorn": {
                    "()": UTCFormatter,
                    "format": log_format,
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                },
                "uvicorn.access": {
                    "()": UTCFormatter,
                    "format": log_format,
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": sys.stdout,
                },
                "uvicorn": {
                    "class": "logging.StreamHandler",
                    "formatter": "uvicorn",
                    "stream": sys.stdout,
                },
                "uvicorn.access": {
                    "class": "logging.StreamHandler",
                    "formatter": "uvicorn.access",
                    "stream": sys.stdout,
                },
            },
            "loggers": {
                "": {  # Root logger
                    "level": settings.LOG_LEVEL,
                    "handlers": ["default"],
                    "propagate": False,
                },
                "uvicorn": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["uvicorn"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["uvicorn"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["uvicorn.access"],
                    "propagate": False,
                },
                "fastapi": {
                    "level": settings.LOG_LEVEL,
                    "handlers": ["default"],
                    "propagate": False,
                },
            },
        }
    )


def setup_logging() -> structlog.BoundLogger:
    """Setup consistent logging for the entire application."""
    configure_standard_logging()
    configure_structlog()
    return structlog.get_logger()


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)
