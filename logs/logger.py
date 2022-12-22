import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path

from dotenv import load_dotenv

from logs.log_tools.add_context_filter import AddContextFilter
from logs.log_tools.log_formatter import LogFormatter
from logs.log_tools.logger_context import LoggerContext
from logs.slack.slack_handler import SlackHandler


load_dotenv()


LOG_PATH = Path(os.environ["LOG_PATH"]) if "LOG_PATH" in os.environ else Path("data/logs").resolve()
LOG_PATH.mkdir(exist_ok=True, parents=True)
LESS_VERBOSE_LOGGERS = ("gunicorn.error", "uvicorn", "sqlalchemy", "fastapi", "pika")


def setup_logging(task_name):
    # Clean up root logger
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)
    for logger_filter in list(logging.root.filters):
        logging.root.removeFilter(logger_filter)

    # silence verbose loggers
    loggers = {
        logging.getLogger(): logging.INFO
    }

    for logger_name in LESS_VERBOSE_LOGGERS:
        loggers[logging.getLogger(logger_name)] = logging.WARNING

    formatter = LogFormatter()
    context = LoggerContext.instance()

    if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
        '''
        When running with gunicorn the log handlers get suppressed instead of
        passed along to the container manager. This forces the gunicorn handlers
        to be used throughout the project.
        '''
        # Use gunicorn error handlers for root, uvicorn, and fastapi loggers
        for handler in logging.getLogger("gunicorn.error").handlers:
            handler.addFilter(AddContextFilter(context))
            handler.setFormatter(formatter)
        for logger_ in loggers:
            logger_.handlers = logging.getLogger("gunicorn.error").handlers

    output_handlers = []

    # Setup file logging, also DEBUG
    file_output = TimedRotatingFileHandler(LOG_PATH / f"{task_name}.log", interval=24)
    file_output.addFilter(AddContextFilter(context))
    file_output.setFormatter(formatter)
    file_output.setLevel(logging.DEBUG)
    output_handlers.append(file_output)

    # Setup stderr logging output, only INFO
    console_output = logging.StreamHandler()
    console_output.addFilter(AddContextFilter(context))
    console_output.setFormatter(formatter)
    output_handlers.append(console_output)

    if os.environ.get("SLACK_URL"):
        slack_output = SlackHandler()
        slack_output.addFilter(AddContextFilter(context))
        slack_output.setFormatter(formatter)
        slack_output.setLevel(logging.ERROR)
        output_handlers.append(slack_output)

    # Pass on logging levels
    for logger_, level in loggers.items():
        logger_.setLevel(level)
        for handler in output_handlers:
            logger_.addHandler(handler)
