import csv
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from fastapi import Request
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from crawlers.base_crawler import BaseCrawler

EQUITY_SCREENER_URL = "https://finance.yahoo.com/research-hub/screener/equity/"

logger = logging.getLogger(__name__)


class FinancialYahoo:
    WAIT_SECONDS = 20
    MAX_PAGES = 100

    def get_attrs(self, request: Request, region: str) -> dict[str, Any]:
        crawler = BaseCrawler()
        normalized_region = region.title()

        driver: WebDriver | None = None
        browser = "Unknown"

        try:
            driver, browser = crawler._start_session(request)
            logger.info(
                "Starting Yahoo crawler for region=%s using browser=%s",
                normalized_region,
                browser,
            )

            driver.get(EQUITY_SCREENER_URL)
            self._accept_cookies(driver)

            return {
                "browser": browser,
                "region": normalized_region,
            }
        finally:
            crawler._finish_session(driver)

    def generate_csv(self, request: Request, region: str) -> dict[str, Any]:
        return self.get_attrs(request, region)

    def _accept_cookies(self, driver: WebDriver) -> None:
        selectors = [
            (By.XPATH, "//button[contains(., 'Accept all')]"),
            (By.XPATH, "//button[contains(., 'Accept All')]"),
            (By.XPATH, "//button[contains(., 'I agree')]"),
            (By.XPATH, "//button[contains(., 'Agree')]"),
        ]
        for by, selector in selectors:
            elements = driver.find_elements(by, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    self._safe_click(driver, element)
                    return

    def _safe_click(self, driver: WebDriver, element: WebElement) -> None:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        driver.execute_script("arguments[0].click();", element)
