import logging

from logcheck.log_tools.logger_context import LoggerContext


class AddContextFilter(logging.Filter):
    def __init__(self, context: LoggerContext, name='', default=None):
        super(AddContextFilter, self).__init__(name)
        self._context = context
        self.default = default or {}

    def filter(self, record):
        record.identifier = self._context.identifier or ''
        return True
