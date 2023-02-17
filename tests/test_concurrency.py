from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool
from pathlib import Path
import sqlite3

from logcheck.slack_handler import INIT_SQL_TABLE


class DummyLogger:

    db_file = Path(__file__).parent / "logcheck_test.cache"

    def __init__(self) -> None:
        self.cache = sqlite3.connect(self.db_file)
        self.cur = self.cache.cursor()
        try:
            self.cur.execute(INIT_SQL_TABLE)
        except sqlite3.OperationalError as ex:
            if "database is locked" not in str(ex):
                raise
    
    def get_cache(self, key):
        res = self.cur.execute("SELECT timestamp FROM cached_log_messages WHERE message=?;", [key]).fetchone()
        return res[0] if res is not None else 0

    def set_cache(self, key, value):
        try:
            self.cur.execute("INSERT INTO cached_log_messages VALUES (?, ?);", [key, value])
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            self.cur.execute("UPDATE cached_log_messages SET timestamp=? WHERE message=?;", [value, key])

        self.cache.commit()

    @staticmethod
    def clean():
        if DummyLogger.db_file.is_file():
            DummyLogger.db_file.unlink(missing_ok=True)


def thread_complex_get_cache(key):
    logger = DummyLogger()
    return logger.get_cache(key)


def thread_complex_log_task(key, value):
    logger = DummyLogger()
    logger.set_cache(key, value)
    pool = Pool(1)
    process = pool.apply_async(thread_complex_get_cache, [key])
    result = process.get()
    pool.close()
    pool.join()
    return result == value


def log_task(value, key='log_message'):
    logger = DummyLogger()
    logger.set_cache(key, value)
    assert logger.get_cache(key) == value


def test_sync():
    log_task("value", "key")
    assert DummyLogger().get_cache("key") == "value"
    DummyLogger.clean()


def test_async():
    p = Pool(4)
    p.starmap(log_task, [(1,), (2,), (3,), (4,)])
    DummyLogger.clean()


def test_async_big_data():
    p = Pool(4)
    p.starmap(log_task, [(i, f'log_message_{i}') for i in range(10000)])

    cache = sqlite3.connect(DummyLogger.db_file)
    cur = cache.cursor()
    assert len(cur.execute("SELECT * FROM cached_log_messages").fetchall()) == 10000
    DummyLogger.clean()


def test_thread_in_thread():
    executor = ProcessPoolExecutor()
    res = executor.map(thread_complex_log_task, ("1", "2", "3"), ("x", "x", "x"))
    assert all(res)
    DummyLogger.clean()
