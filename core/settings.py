from dotenv import load_dotenv
from yarl import URL

from .enums import Mode

from pathlib import Path
from typing import Final
import hashlib
import logging.config
import os
import secrets

load_dotenv()


BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
LOGS_DIR: Final[Path] = BASE_DIR / 'logs' / 'platform-bot'

os.makedirs(LOGS_DIR, exist_ok=True)


MODE: Final[Mode] = Mode(os.getenv('MODE', Mode.DEBUG).lower())

USER_AGENT: Final[str] = 'ConstructorTelegramBots (constructor.exg1o.org; platform-bot)'
REDIS_URL: Final[str] = os.environ['REDIS_URL']
BOT_TOKEN: Final[str] = os.environ['BOT_TOKEN']
TELEGRAM_TOKEN: Final[str] = secrets.token_hex(32)

APP_URL: Final[URL] = URL(os.environ['APP_URL'])
APP_TOKEN: Final[str] = hashlib.sha256(BOT_TOKEN.encode()).hexdigest()

SERVICE_URL: Final[URL] = URL(os.environ['SERVICE_URL'])
SERVICE_SOCKET: Final[Path | None] = (
    Path(path) if (path := os.getenv('SERVICE_SOCKET')) else None
)
SERVICE_TOKEN: Final[str] = APP_TOKEN


logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[{asctime}]: {levelname}: {name} > {funcName} || {message}',
                'style': '{',
            },
            'simple': {
                'format': '[{asctime}]: {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'info_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'app_info.log',
                'maxBytes': 2.5 * 1024**2,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'app_error.log',
                'maxBytes': 2.5 * 1024**2,
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['console', 'info_file', 'error_file'],
            'level': 'DEBUG' if MODE == Mode.DEBUG else 'INFO',
        },
    }
)
