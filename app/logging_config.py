"""
Configuration globale de structlog — redirige vers stderr
pour éviter les BrokenPipeError avec uvicorn --reload.
"""
import sys
import structlog


def setup_logging():
    """Configure structlog pour écrire sur stderr (pas stdout)."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
