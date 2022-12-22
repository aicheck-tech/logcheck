from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from pytz import timezone, utc


load_dotenv()

TIMEZONE = timezone(os.environ.get("TIMEZONE", "utc"))


class LogFormatter(logging.Formatter):

    def __init__(self):
        self.converter = self._get_local_time
        super().__init__(fmt="%(asctime)s %(levelname)s %(message)s")

    def format(self, record):
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        original_format = self._style._fmt

        # Replace the original format with one customized by logging level
        self._style._fmt = "%(asctime)s %(transaction_id)s %(levelname)s %(message)s"

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = original_format
        return result

    @staticmethod
    def _get_local_time(*args):
        """Get TIMEZONE time. Use with logging to get local time instead of server time (usually UTC).

        Args:
            *args (Any): compatibility reasons to have args
        """
        utc_dt = utc.localize(datetime.utcnow())
        converted = utc_dt.astimezone(TIMEZONE)
        return converted.timetuple()
