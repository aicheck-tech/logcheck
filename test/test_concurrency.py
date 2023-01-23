
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import os
from pathlib import Path
import sqlite3

class Logger:
    def __init__(self) -> None:
        self.cache = sqlite3.connect("./test/logcheck_test.cache")
        self.cur = self.cache.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS logs(key TEXT PRIMARY KEY, time NUMERIC);")
    
    def get_cache(self, key):
        res = self.cur.execute("SELECT time FROM logs WHERE key=?;", [key]).fetchone()
        return res[0] if res is not None else 0

    def set_cache(self, key, value):
        try:
            self.cur.execute("INSERT INTO logs VALUES (?, ?);", [key, value])
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            self.cur.execute("UPDATE logs SET time=? WHERE key=?;", [value, key])

        self.cache.commit()


def log_task(value, key='log_message'):
    logger = Logger()
    logger.set_cache(key, value)
    assert logger.get_cache(key) == value


def test_logger():
    p = Pool(4)
    p.starmap(log_task, [(1,), (2,), (3,), (4,)])

    os.remove("./test/logcheck_test.cache")


def test_logger_big_data():
    p = Pool(4)
    p.starmap(log_task, [(i, f'log_message_{i}') for i in range(1000)])

    cache = sqlite3.connect("./test/logcheck_test.cache")
    cur = cache.cursor()
    assert len(cur.execute("SELECT * FROM logs").fetchall()) == 1000

    os.remove("./test/logcheck_test.cache")
