import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pygit2 import Repository, GitError

from logcheck.add_context_filter import AddContextFilter
from logcheck.log_formatter import LogFormatter
from logcheck.logger_context import LoggerContext
from logcheck.slack.slack_handler import SlackHandler


load_dotenv()


LESS_VERBOSE_LOGGERS = ("gunicorn.error", "uvicorn", "sqlalchemy", "fastapi", "pika")
if "LOG_PATH" in os.environ:
    LOG_PATH = Path(os.environ["LOG_PATH"])
else:
    try:
        LOG_PATH = Path(Repository('').workdir).resolve() / "data" / "logs"
    except GitError:
        LOG_PATH = Path("").resolve() / "data" / "logs"

LOG_PATH.mkdir(exist_ok=True, parents=True)


def setup_logging(task_name: str) -> logging.Logger:
    """Setup loggers to output to rotated file, standard output and optionally to slack.
    Call at least once in the beginning of the script to enable correct logging.

    Args:
        task_name: String description (ASCII) of logged task,
                   save logs to file named `task_name`,
                   slack integration uses string `task_name` in message.

    Returns:
        root logger
    """
    if not isinstance(task_name, str):
        raise ValueError(f"Cannot init logging with non-string task_name=`{task_name}`.")

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
        slack_output = SlackHandler(name=task_name)
        slack_output.addFilter(AddContextFilter(context))
        slack_output.setFormatter(formatter)
        slack_output.setLevel(logging.ERROR)
        output_handlers.append(slack_output)

    # Pass on logging levels
    for logger_, level in loggers.items():
        logger_.setLevel(level)
        for handler in output_handlers:
            logger_.addHandler(handler)

    if not os.environ.get("SLACK_URL"):
        logging.getLogger().warning("Slack logging turned off.")

    return logging.getLogger()


def set_task_context(identifier: Optional[str] = None):
    """Modify logging format to output `identifier` to every message in current thread.

    Args:
        identifier: Any string describing current process. Use default None if there is no such string.

    """
    if identifier:
        LoggerContext.instance().set(identifier=identifier)
    else:
        LoggerContext.instance().set(identifier=None)
