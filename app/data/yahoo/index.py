import asyncio
import logging

import yfinance
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.common.enum import MarketIndexEnum
from app.data.yahoo.source.constant import MARKET_TIME_INTERVAL
from app.data.yahoo.source.service import get_last_week_period_bounds
from app.module.asset.model import MarketIndexDaily
from app.module.asset.repository.market_index_daily_repository import MarketIndexDailyRepository
from database.dependency import get_mysql_session

logger = logging.getLogger("index")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("/home/backend/index.log", delay=False)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)


async def fetch_and_save_market_index_data(
    session: AsyncSession,
    index_symbol: str,
    start_period: str,
    end_period: str,
):
    index_data = yfinance.download(
        index_symbol, start=start_period, end=end_period, interval=MARKET_TIME_INTERVAL, progress=False
    )

    if index_data and index_data.empty:
        return

    market_index_records = []

    for index, row in index_data.iterrows():
        market_index_record = MarketIndexDaily(
            name=index_symbol.lstrip("^"),
            date=index.date(),
            open_price=row["Open"],
            close_price=row["Close"],
            high_price=row["High"],
            low_price=row["Low"],
            volume=row["Volume"],
        )
        market_index_records.append(market_index_record)

    if market_index_records:
        await MarketIndexDailyRepository.bulk_upsert(session, market_index_records)


async def fetch_and_save_all_intervals(session: AsyncSession, index_symbol: str, start_period: str, end_period: str):
    await fetch_and_save_market_index_data(session, index_symbol, start_period, end_period)


async def execute_async_task():
    logger.info("일별 시장 지수 수집을 시작합니다.")
    start_period, end_period = get_last_week_period_bounds()

    async with get_mysql_session() as session:
        for index_symbol in MarketIndexEnum:
            await fetch_and_save_all_intervals(session, index_symbol, start_period, end_period)

    logger.info("일별 시장 지수 수집을 마칩니다.")


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
