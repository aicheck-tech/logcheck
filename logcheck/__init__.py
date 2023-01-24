from logcheck.logger import set_task_context, setup_logging

SQL_cache_create = (
    "CREATE TABLE IF NOT EXISTS cached_log_messages ( \
        message       TEXT          PRIMARY KEY, \
        timestamp     NUMERIC       not null \
    );"
)