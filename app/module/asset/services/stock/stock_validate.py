from app.common.util.time import get_now_date
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.repository.stock_daily_repository import StockDailyRepository
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

class StockValidate:
    async def check_code_exist(self, session: AsyncSession, code:str) -> bool:
        stock = await StockRepository.get_by_code(session, code)
        return True if stock else False
        
    async def check_stock_data_exist(self, session: AsyncSession, code:str, buy_date:date) -> bool:
        # 오늘 날짜는 일별 데이터가 미 수집 상태라 허용합니다.
        if buy_date == get_now_date():
            return True
        
        stock = await StockDailyRepository.get_stock_daily(session, code, buy_date)
        return True if stock else False
        
        
        