from core.settings import BASE_DIR, LOGS_DIR

from typing import Final

worker_class: Final[str] = 'uvicorn.workers.UvicornWorker'
workers: Final[int] = 1
threads: Final[int] = 1

bind: Final[str] = f'unix:{BASE_DIR / "sockets" / "platform-bot.sock"}'

capture_output: Final[bool] = True
accesslog: Final[str] = str(LOGS_DIR / 'gunicorn.log')
errorlog: Final[str] = str(LOGS_DIR / 'gunicorn.log')
