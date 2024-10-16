from os import getenv
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from database.enum import EnvironmentType

import app.data.tip.run  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.dividend 
import app.data.yahoo.index 
import app.data.yahoo.stock 
import app.data.investing.rich_portfolio
import app.data.yahoo.exchange_rate
import app.data.naver.realtime_index_korea
import app.data.naver.realtime_index_world

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)
if ENVIRONMENT == EnvironmentType.DEV:
    REDIS_HOST = getenv("LOCAL_REDIS_HOST", None)
else:
    REDIS_HOST = getenv("REDIS_HOST", None)

REDIS_PORT = getenv("REDIS_PORT", None)

celery_task = Celery(
    "celery_schedule", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}", backend=f"redis://{REDIS_HOST}:{REDIS_PORT}"
)

celery_task.conf.timezone = "Asia/Seoul"
celery_task.conf.enable_utc = False


celery_task.conf.beat_schedule = {
    "tip": {
        "task": "app.data.tip.run.main",
        "schedule": crontab(hour=22, minute=53),
    },
    "dividend": {
        "task": "app.data.yahoo.dividend.main",
        "schedule": crontab(hour=22, minute=53),
    },
    "index": {
        "task": "app.data.yahoo.index.main",
        "schedule": crontab(hour=22, minute=53),
    },
    "stock": {
        "task": "app.data.yahoo.stock.main",
        "schedule": crontab(hour=22, minute=53),
    },
    "rich_portfolio": {
        "task": "app.data.investing.rich_portfolio.main",
        "schedule": crontab(hour=22, minute=56),
    },
    "exchange_rate": {
        "task": "app.data.yahoo.exchange_rate.main",
        "schedule": crontab(hour=23, minute=8),
        "options": {"run_once": True},
    },
    "realtime_index_korea_everyday": {
        "task": "app.data.naver.realtime_index_korea.main",
        "schedule": crontab(hour=23, minute=25),
        "options": {"run_once": True},
    },
    "realtime_index_world_everyday": {
        "task": "app.data.naver.realtime_index_world.main",
        "schedule": crontab(hour=23, minute=30),
        "options": {"run_once": True},
    },
    # "realtime_stock_run_everyday": {
    #     "task": "app.data.yahoo.realtime_stock_run.main",
    #     "schedule": crontab(hour=0, minute=0),
    #     "options": {"run_once": True},
    # },
}
