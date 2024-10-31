from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.model import Asset, Dividend
from app.module.asset.repository.dividend_repository import DividendRepository
from app.module.asset.services.exchange_rate_service import ExchangeRateService


class DividendService:
    def get_closest_dividend_temp(self, asset: Asset, dividend_map: dict[tuple[str, date], float]) -> date | None:
        asset_code: str = asset.asset_stock.stock.code
        asset_date: date = asset.asset_stock.purchase_date

        filtered_dividends = sorted(
            (
                (dividend_date, dividend_amount)
                for (dividend_code, dividend_date), dividend_amount in dividend_map.items()
                if dividend_code == asset_code and dividend_date > asset_date
            ),
            key=lambda x: x[0],
        )

        return filtered_dividends[0][0] if filtered_dividends else None

    
    def process_dividends_by_year_month_temp(self, total_dividends: dict[date, float]) -> dict[str, dict[int, float]]:
        dividend_by_year_month: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))

        for dividend_date, dividend_amount in total_dividends.items():
            dividend_by_year_month[dividend_date.year][dividend_date.month] += dividend_amount

        result = {}
        for year, months in dividend_by_year_month.items():
            result[str(year)] = {month: months.get(month, 0.0) for month in range(1, 13)}

        return result

    
    def get_last_year_dividends_temp(
        self,
        asset: Asset,
        dividend_map: dict[tuple[str, date], float],
        won_exchange_rate: float,
        last_dividend_date: date,
    ) -> defaultdict[date, float]:
        result: defaultdict[date, float] = defaultdict(float)
        last_year = last_dividend_date.year - 1
        last_year_dividend_date = last_dividend_date.replace(year=last_year) + timedelta(days=1)

        for (dividend_code, dividend_date), dividend_amount in dividend_map.items():
            if (
                dividend_code == asset.asset_stock.stock.code
                and dividend_date >= last_year_dividend_date
                and dividend_date <= date(last_year, 12, 31)
            ):
                new_dividend_date = dividend_date.replace(year=last_dividend_date.year)
                dividend_kr = dividend_amount * won_exchange_rate * asset.asset_stock.quantity
                result[new_dividend_date] += dividend_kr

        return result

    
    def get_asset_total_dividend_temp(
        self,
        won_exchange_rate: float, 
        dividend_map: dict[tuple[str, date], float], 
        asset: Asset
    ) -> tuple[defaultdict[date, float], date | None]:
        result: defaultdict[date, float] = defaultdict(float)
        last_dividend_date: date | None = None

        for code_date_key, dividend_amount in dividend_map.items():
            dividend_code, dividend_date = code_date_key
            if dividend_code == asset.asset_stock.stock.code and dividend_date >= asset.asset_stock.purchase_date:
                dividend_kr = dividend_amount * won_exchange_rate * asset.asset_stock.quantity
                result[dividend_date] += dividend_kr
                last_dividend_date = dividend_date

        return result, last_dividend_date

    
    async def get_dividend_map_temp(self, session: AsyncSession, assets: list[Asset]) -> dict[tuple[str, date], float]:
        stock_codes = [asset.asset_stock.stock.code for asset in assets]
        dividends: list[Dividend] = await DividendRepository.get_dividends(session, stock_codes)

        return {
            (dividend.stock_code, dividend.date): dividend.dividend
            for dividend in dividends
            if isinstance(dividend.date, date) and str(dividend.date) != "0000-00-00"
        }

    
    async def get_recent_map_temp(self, session: AsyncSession, assets: list[Asset]) -> dict[str, float]:
        stock_codes = [asset.asset_stock.stock.code for asset in assets]
        dividends: list[Dividend] = await DividendRepository.get_dividends_recent(session, stock_codes)

        return {
            dividend.stock_code: dividend.dividend
            for dividend in dividends
            if isinstance(dividend.date, date) and str(dividend.date) != "0000-00-00"
        }

    
    def get_total_dividend_temp(
        self,
        assets: list[Asset], 
        dividend_map: dict[str, float], 
        exchange_rate_map: dict[str, float]
    ) -> float:
        total_dividend_amount = 0.0

        for asset in assets:
            total_dividend_amount += (
                dividend_map.get(asset.asset_stock.stock.code, 0.0)
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return total_dividend_amount

    
    
    ##################   staticmethod는 차츰 변경하겠습니다!   ##################
    
    
    
    @staticmethod
    def get_closest_dividend(asset: Asset, dividend_map: dict[tuple[str, date], float]) -> date | None:
        asset_code: str = asset.asset_stock.stock.code
        asset_date: date = asset.asset_stock.purchase_date

        filtered_dividends = sorted(
            (
                (dividend_date, dividend_amount)
                for (dividend_code, dividend_date), dividend_amount in dividend_map.items()
                if dividend_code == asset_code and dividend_date > asset_date
            ),
            key=lambda x: x[0],
        )

        return filtered_dividends[0][0] if filtered_dividends else None

    @staticmethod
    def process_dividends_by_year_month(total_dividends: dict[date, float]) -> dict[str, dict[int, float]]:
        dividend_by_year_month: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))

        for dividend_date, dividend_amount in total_dividends.items():
            dividend_by_year_month[dividend_date.year][dividend_date.month] += dividend_amount

        result = {}
        for year, months in dividend_by_year_month.items():
            result[str(year)] = {month: months.get(month, 0.0) for month in range(1, 13)}

        return result

    @staticmethod
    def get_last_year_dividends(
        asset: Asset,
        dividend_map: dict[tuple[str, date], float],
        won_exchange_rate: float,
        last_dividend_date: date,
    ) -> defaultdict[date, float]:
        result: defaultdict[date, float] = defaultdict(float)
        last_year = last_dividend_date.year - 1
        last_year_dividend_date = last_dividend_date.replace(year=last_year) + timedelta(days=1)

        for (dividend_code, dividend_date), dividend_amount in dividend_map.items():
            if (
                dividend_code == asset.asset_stock.stock.code
                and dividend_date >= last_year_dividend_date
                and dividend_date <= date(last_year, 12, 31)
            ):
                new_dividend_date = dividend_date.replace(year=last_dividend_date.year)
                dividend_kr = dividend_amount * won_exchange_rate * asset.asset_stock.quantity
                result[new_dividend_date] += dividend_kr

        return result

    @staticmethod
    def get_asset_total_dividend(
        won_exchange_rate: float, dividend_map: dict[tuple[str, date], float], asset: Asset
    ) -> tuple[defaultdict[date, float], date | None]:
        result: defaultdict[date, float] = defaultdict(float)
        last_dividend_date: date | None = None

        for code_date_key, dividend_amount in dividend_map.items():
            dividend_code, dividend_date = code_date_key
            if dividend_code == asset.asset_stock.stock.code and dividend_date >= asset.asset_stock.purchase_date:
                dividend_kr = dividend_amount * won_exchange_rate * asset.asset_stock.quantity
                result[dividend_date] += dividend_kr
                last_dividend_date = dividend_date

        return result, last_dividend_date

    @staticmethod
    async def get_dividend_map(session: AsyncSession, assets: list[Asset]) -> dict[tuple[str, date], float]:
        stock_codes = [asset.asset_stock.stock.code for asset in assets]
        dividends: list[Dividend] = await DividendRepository.get_dividends(session, stock_codes)

        return {
            (dividend.stock_code, dividend.date): dividend.dividend
            for dividend in dividends
            if isinstance(dividend.date, date) and str(dividend.date) != "0000-00-00"
        }

    @staticmethod
    async def get_recent_map(session: AsyncSession, assets: list[Asset]) -> dict[str, float]:
        stock_codes = [asset.asset_stock.stock.code for asset in assets]
        dividends: list[Dividend] = await DividendRepository.get_dividends_recent(session, stock_codes)

        return {
            dividend.stock_code: dividend.dividend
            for dividend in dividends
            if isinstance(dividend.date, date) and str(dividend.date) != "0000-00-00"
        }

    @staticmethod
    def get_total_dividend(
        assets: list[Asset], dividend_map: dict[str, float], exchange_rate_map: dict[str, float]
    ) -> float:
        total_dividend_amount = 0.0

        for asset in assets:
            total_dividend_amount += (
                dividend_map.get(asset.asset_stock.stock.code, 0.0)
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return total_dividend_amount
