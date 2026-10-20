import logging.config


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging; uvicorn keeps its own handlers."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"}
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"level": level.upper(), "handlers": ["console"]},
        }
    )
