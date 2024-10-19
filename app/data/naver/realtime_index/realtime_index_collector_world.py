import asyncio

import ray
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.common.util.time import get_now_datetime
from app.data.common.constant import MARKET_INDEX_CACHE_SECOND
from app.data.yahoo.source.constant import REALTIME_INDEX_COLLECTOR_WAIT_SECOND
from app.module.asset.constant import COUNTRY_TRANSLATIONS, INDEX_NAME_TRANSLATIONS
from app.module.asset.model import MarketIndexMinutely
from app.module.asset.redis_repository import RedisRealTimeMarketIndexRepository
from app.module.asset.repository.market_index_minutely_repository import MarketIndexMinutelyRepository
from app.module.asset.schema import MarketIndexData
from database.dependency import get_mysql_session, get_redis_pool


@ray.remote
class RealtimeIndexWorldCollector:
    def __init__(self):
        self.redis_client = None
        self.session = None
        self._is_running = False

    async def _setup(self):
        self.redis_client = get_redis_pool()
        async with get_mysql_session() as session:
            self.session = session

    async def collect(self):
        if self.redis_client is None or self.session is None:
            await self._setup()
        try:
            while True:
                self._is_running = True
                await self._fetch_market_data()
                await asyncio.sleep(REALTIME_INDEX_COLLECTOR_WAIT_SECOND)
                self._is_running = False
        except Exception:
            self._is_running = False

    async def _fetch_market_data(self):
        driver = await self._init_webdriver()

        try:
            driver.get("https://finance.naver.com/world/")
            redis_bulk_data, db_bulk_data = [], []

            america_index_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "americaIndex"))
            )
            tr_rows = america_index_table.find_elements(By.XPATH, ".//thead/tr")

            for tr_row in tr_rows:
                market_data = self._parse_tr_row(tr_row)
                if market_data:
                    redis_bulk_data.append(market_data["redis"])
                    db_bulk_data.append(market_data["db"])

            await self._save_market_data(db_bulk_data, redis_bulk_data)
        finally:
            driver.quit()

    async def _init_webdriver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def _parse_tr_row(self, tr_row):
        tds = tr_row.find_elements(By.TAG_NAME, "td")
        tr_row_data = []

        for td in tds:
            if "graph" in td.get_attribute("class"):
                continue

            span = td.find_elements(By.TAG_NAME, "span")
            if span:
                tr_row_data.append(span[0].text)
            else:
                a_elements = td.find_elements(By.TAG_NAME, "a")
                if a_elements:
                    tr_row_data.append(a_elements[0].text)
                else:
                    tr_row_data.append(td.text)

        if tr_row_data:
            country_kr = tr_row_data[0]
            if country_kr in COUNTRY_TRANSLATIONS:
                country_en = COUNTRY_TRANSLATIONS[country_kr]
            else:
                return None

            name_kr = tr_row_data[1]
            name_en = INDEX_NAME_TRANSLATIONS.get(name_kr, name_kr)

            current_value = tr_row_data[2].strip().replace(",", "")
            change_value = tr_row_data[3].strip().replace(",", "")
            change_percent = tr_row_data[4].strip().replace("%", "")

            market_index = MarketIndexData(
                country=country_en,
                name=name_en,
                current_value=current_value,
                change_value=change_value,
                change_percent=change_percent,
                update_time=tr_row_data[5],
            )

            current_index = MarketIndexMinutely(name=name_en, datetime=get_now_datetime(), current_price=current_value)

            return {"redis": (name_en, market_index.model_dump_json()), "db": current_index}

        return None

    async def _save_market_data(self, db_bulk_data, redis_bulk_data):
        await MarketIndexMinutelyRepository.bulk_upsert(self.session, db_bulk_data)
        await RedisRealTimeMarketIndexRepository.bulk_save(
            self.redis_client, redis_bulk_data, expire_time=MARKET_INDEX_CACHE_SECOND
        )

    def is_running(self) -> bool:
        return self._is_running
