import logging
import socket
import tempfile
import time
import sqlite3
from pathlib import Path
from typing import Optional

import pygit2.errors
from pygit2 import Repository

from logcheck.slack_integration import SlackIntegration


SQL_cache_create = (
    "CREATE TABLE IF NOT EXISTS cached_log_messages ( \
        message       TEXT          PRIMARY KEY, \
        timestamp     NUMERIC       not null \
    );"
)


class TLogRecord(logging.LogRecord):
    identifier: Optional[str]


class SlackHandler(logging.Handler):

    MIN_DELAY_BETWEEN_ERRORS = 3600

    def __init__(self, name: Optional[str] = None):
        self.slack_tool = SlackIntegration()
        self.host_name = socket.gethostname()
        self.cache = sqlite3.connect((Path(tempfile.gettempdir()) / ".slack_handler.cache").resolve())
        self.cur = self.cache.cursor()
        try:
            self.cur.execute(SQL_cache_create)
        except sqlite3.OperationalError as ex:
            if "database is locked" not in str(ex):  # lock means table already exists
                raise

        self.task_name = name
        super().__init__()

    def emit(self, record: TLogRecord) -> None:
        try:
            current_repo = Repository(Path(".").resolve())
            git_text_ = f"{current_repo.head.shorthand}@{self.host_name}:{current_repo.workdir}"
        except pygit2.errors.GitError:
            git_text_ = "nogit"

        incident_at_ = f"{record.pathname}:{record.lineno}"
        if record.funcName != "<module>":
            incident_at_ += " " + record.funcName

        description_ = record.message if record.message else ""
        try:
            error_name_ = record.exc_info[0].__name__
        except TypeError:
            error_name_ = "ERROR"
        if self.task_name and record.identifier:
            identifier = f" `[{self.task_name}:{record.identifier}]`"
        elif self.task_name:
            identifier = f" `[{self.task_name}]`"
        elif record.identifier:
            identifier = f" `[{record.identifier}]`"
        else:
            identifier = ""

        msg = f"_{record.asctime}_ _{error_name_}_{identifier} `{incident_at_}` *{git_text_}* {description_}".strip()
        cache_key = f"{identifier}/{incident_at_}/{git_text_}/{description_}"

        if time.time() - self.get_cache(cache_key) >= self.MIN_DELAY_BETWEEN_ERRORS:
            self.set_cache(cache_key, time.time())
            code = None
            if record.exc_info:
                code = record.exc_text
            self.slack_tool.send_slack_msg(msg, code=code)

    def get_cache(self, key):
        res = self.cur.execute("SELECT timestamp FROM cached_log_messages WHERE message=?;", [key]).fetchone()
        return res[0] if res is not None else 0

    def set_cache(self, key, value):
        try:
            self.cur.execute("INSERT INTO cached_log_messages VALUES (?, ?);", [key, value])
        except sqlite3.IntegrityError:
            self.cur.execute("UPDATE cached_log_messages SET timestamp=? WHERE message=?;", [value, key])

        self.cache.commit()
