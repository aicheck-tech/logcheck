import threading
from typing import Optional


class LoggerContext(threading.local):
    _instance: 'LoggerContext' = None

    def __init__(self):
        self.transaction_id: Optional[str] = None

    # Allow only a single instance of this object to exist in a thread
    @classmethod
    def instance(cls) -> 'LoggerContext':
        if cls._instance is None:
            cls._instance = LoggerContext()
        return cls._instance

    @classmethod
    def set(cls, *, transaction_id: str):
        cls.instance().transaction_id = transaction_id

    @classmethod
    def reset(cls):
        cls.instance().transaction_id = None
