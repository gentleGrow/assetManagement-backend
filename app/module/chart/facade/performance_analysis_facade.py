from collections import defaultdict
from datetime import date, datetime, time, timedelta
from math import floor

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType, MarketIndex
from app.module.asset.model import MarketIndexMinutely, StockDaily, StockMinutely
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.current_index_service import CurrentIndexService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.market_index_daily_service import MarketIndexDailyService
from app.module.asset.services.market_index_minutely_service import MarketIndexMinutelyService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService
from app.module.chart.enum import IntervalType


class PerformanceAnalysisFacade:
    @staticmethod
    async def get_market_analysis(
        session: AsyncSession, redis_client: Redis, start_date: date, end_date: date
    ) -> dict[date, float]:
        adjusted_start_date = start_date - timedelta(days=7)
        market_index_date_map = await MarketIndexDailyService.get_market_index_date_map(
            session, (adjusted_start_date, end_date), MarketIndex.KOSPI
        )
        current_kospi_price = await CurrentIndexService.get_current_index_price(redis_client, MarketIndex.KOSPI)
        result = {}
        current_profit = 0.0
        current_date = adjusted_start_date

        while current_date <= end_date:
            if current_date in market_index_date_map:
                market_index = market_index_date_map[current_date]
                current_profit = ((current_kospi_price - market_index.close_price) / market_index.close_price) * 100

            if current_date > start_date:
                result[current_date] = current_profit
            current_date += timedelta(days=1)

        return result

    @staticmethod
    async def get_user_analysis(
        session: AsyncSession,
        redis_client: Redis,
        interval_start: date,
        interval_end: date,
        user_id: int,
        market_analysis_result: dict[date, float],
    ) -> dict[date, float]:
        assets = await AssetRepository.get_eager_by_range(
            session, user_id, AssetType.STOCK, (interval_start, interval_end)
        )

        stock_daily_map: dict[tuple[str, date], StockDaily] = await StockDailyService.get_map_range(
            session,
            assets,
        )
        latest_stock_daily_map: dict[str, StockDaily] = await StockDailyService.get_latest_map(session, assets)
        current_stock_price_map = await StockService.get_current_stock_price_by_code(
            redis_client, latest_stock_daily_map, [asset.asset_stock.stock.code for asset in assets]
        )
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)

        assets_by_date = defaultdict(list)
        for asset in assets:
            assets_by_date[asset.asset_stock.purchase_date].append(asset)

        cumulative_assets = []
        result = {}

        current_profit = 0.0

        for market_date in sorted(market_analysis_result):
            if market_date in assets_by_date:
                assets_for_date = assets_by_date[market_date]
                cumulative_assets.extend(assets_for_date)

                total_asset_amount = AssetStockService.get_total_asset_amount(
                    cumulative_assets, current_stock_price_map, exchange_rate_map
                )
                total_invest_amount = AssetStockService.get_total_investment_amount(
                    cumulative_assets, stock_daily_map, exchange_rate_map
                )
                current_profit = (
                    ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
                    if total_invest_amount > 0.0 and total_asset_amount > 0.0
                    else 0.0
                )
                result[market_date] = (
                    ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
                    if total_invest_amount > 0.0 and total_asset_amount > 0.0
                    else 0.0
                )
            else:
                result[market_date] = current_profit

        return result

    @staticmethod
    async def get_user_analysis_short(
        session: AsyncSession,
        redis_client: Redis,
        interval_start: datetime,
        interval_end: datetime,
        user_id: int,
        interval: IntervalType,
        market_analysis_result: dict[datetime, float],
    ) -> dict[datetime, float]:
        assets = await AssetRepository.get_eager_by_range(
            session, user_id, AssetType.STOCK, (interval_start, interval_end)
        )

        stock_daily_map = await StockDailyService.get_map_range(session, assets)
        exchange_rate_map: dict[str, float] = await ExchangeRateService.get_exchange_rate_map(redis_client)

        interval_data: list[StockMinutely] = await StockMinutelyRepository.get_by_range_interval_minute(
            session,
            (interval_start, interval_end),
            [asset.asset_stock.stock.code for asset in assets],
            interval.get_interval(),
        )

        stock_interval_date_price_map = {
            f"{stock_minutely.code}_{stock_minutely.datetime}": stock_minutely.current_price
            for stock_minutely in interval_data
        }

        assets_by_date = defaultdict(list)
        for asset in assets:
            purchase_datetime = datetime.combine(asset.asset_stock.purchase_date, time.max)
            assets_by_date[purchase_datetime].append(asset)

        result = {}
        cumulative_assets = []

        for market_datetime in sorted(market_analysis_result):
            if market_datetime in assets_by_date:
                assets_for_date = assets_by_date[market_datetime]
                cumulative_assets.extend(assets_for_date)

            total_asset_amount = AssetStockService.get_total_asset_amount_minute(
                assets, stock_interval_date_price_map, exchange_rate_map, market_datetime
            )

            total_invest_amount = AssetStockService.get_total_investment_amount(
                cumulative_assets, stock_daily_map, exchange_rate_map
            )

            total_profit_rate = 0.0
            if total_invest_amount > 0:
                total_profit_rate = ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100

            result[market_datetime] = total_profit_rate

        return result

    @staticmethod
    async def get_market_analysis_short(
        session: AsyncSession,
        redis_client: Redis,
        interval_start: datetime,
        interval_end: datetime,
        interval: IntervalType,
    ) -> dict[datetime, float]:
        market_index_minutely_map: dict[
            datetime, MarketIndexMinutely
        ] = await MarketIndexMinutelyService.get_index_range_interval_map(
            session, MarketIndex.KOSPI, (interval_start, interval_end), interval
        )
        current_kospi_price = await CurrentIndexService.get_current_index_price(redis_client, MarketIndex.KOSPI)

        result = {}

        minutes_offset = interval_start.minute % interval.get_interval()

        if minutes_offset != 0:
            adjusted_minutes = floor(interval_start.minute / interval.get_interval()) * interval.get_interval()
            interval_start = interval_start.replace(minute=adjusted_minutes, second=0, microsecond=0)

        current_datetime = interval_start

        current_profit = 0.0

        while current_datetime <= interval_end:
            naive_current_datetime = current_datetime.replace(tzinfo=None)

            if naive_current_datetime in market_index_minutely_map:
                market_index = market_index_minutely_map[naive_current_datetime]
                current_profit = ((current_kospi_price - market_index.current_price) / market_index.current_price) * 100

            result[naive_current_datetime] = current_profit
            current_datetime += timedelta(minutes=interval.get_interval())

        return result
