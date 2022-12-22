import logging

from logs.log_tools.logger_context import LoggerContext


class AddContextFilter(logging.Filter):
    def __init__(self, context: LoggerContext, name='', default=None):
        super(AddContextFilter, self).__init__(name)
        self._context = context
        self.default = default or {}

    def filter(self, record):
        record.transaction_id = self._context.transaction_id or ''
        return True
