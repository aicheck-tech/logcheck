from multiprocessing import Pool
from pathlib import Path
import sqlite3


class DummyLogger:

    db_file = Path(__file__).parent / "logcheck_test.cache"

    def __init__(self) -> None:
        self.cache = sqlite3.connect(self.db_file)
        self.cur = self.cache.cursor()
        try:
            self.cur.execute((Path(__file__).parent.parent / "logcheck" / "cached_log_messages.sql").read_text())
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
