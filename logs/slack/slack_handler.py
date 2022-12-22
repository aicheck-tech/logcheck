import logging
import socket

from pygit2 import Repository

from logs.slack.slack_integration import SlackIntegration


class SlackHandler(logging.Handler):
    def __init__(self):
        self.slack_tool = SlackIntegration()
        self.host_name = socket.gethostname()
        super().__init__()


    def emit(self, record: logging.LogRecord) -> None:
        msg = (
            f"_{record.asctime}_ _{record.exc_info[0].__name__}_ "
            f"`{record.pathname}:{record.lineno}{':' + record.funcName if record.funcName != '<module>' else ''}` "
            f"*{self.host_name}:{Repository('.').head.shorthand}:{record.message}*"
        )

        print(msg)
        code = None
        if record.exc_info:
            code = record.exc_text
        #self.slack_tool.send_slack_msg(msg, code=code)
