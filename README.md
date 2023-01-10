# LogCheck

Simple logging with connector to slack.

## Installation

```bash
pip install git+ssh://git@github.com/aicheck-tech/logcheck.git
touch .env
echo '
LOG_PATH=/data/logs/python-slack-logs
SLACK_URL=https://hooks.slack.com/services/{app}/{token1}/{token2}
SLACK_APP=T01KAMSTFHS
SLACK_TOKEN1=?
SLACK_TOKEN2=?
SLACK_MAPPING={"janrygl": "U01JPPLNUKH", "jiripomikalek": "U02D130H93M"}
' >> .env
```

## Usage

```python
import logging

from logcheck import setup_logging, set_task_context


logger = logging.getLogger(__name__)
setup_logging("some_file_name")

def task(tid: str):
    set_task_context(tid)
    logging.info(f"test {tid}")
    set_task_context(None)


if __name__ == "__main__":    
    task("a")
    task("b")
    task("c")

```
