from concurrent.futures import ThreadPoolExecutor
import json
import os
from typing import Optional

import requests

from dotenv import load_dotenv


load_dotenv()


class SlackIntegration:

    def __init__(self):
        self.url = os.environ["SLACK_URL"].format(
            app=os.environ["SLACK_APP"],
            token1=os.environ["SLACK_TOKEN1"],
            token2=os.environ["SLACK_TOKEN2"]
        )
        self.user_mapping = json.loads(os.environ["SLACK_MAPPING"])
        self.executor = ThreadPoolExecutor(4)

    def send_slack_msg(self, message: str, code: Optional[str] = None, recipient: Optional[str] = None):
        if recipient:
            message = f"<@{self.user_mapping[recipient]}> {message}"
        if code:
            message += f"\n```{code}```"
        self.executor.submit(requests.post, self.url, None, {"text": message})
        