import logging
import time


from bs4 import BeautifulSoup
from fastapi import Request
from selenium.common import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from drivers.edge import Edge
from drivers.firefox import Firefox
from drivers.google_chrome import GoogleChrome
from drivers.opera import Opera
from drivers.safari import Safari
from utils.utils import detect_browser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class BaseCrawler:
    async def _start_session(self, request: Request, headless: bool = False) -> tuple[WebDriver, str]:
        header_info = request.headers.get("user-agent", "")
        browser = detect_browser(header_info)

        browser_map = {
            "Chrome": GoogleChrome,
            "Safari": Safari,
            "Firefox": Firefox,
            "Edge": Edge,
            "Opera": Opera,
        }

        selected_browser = browser_map.get(browser, GoogleChrome)()
        driver = selected_browser.start(headless=headless)
        return driver, browser

    async def _finish_session(self, driver: WebDriver | None) -> None:
        """Always close browser session, even if the crawl fails."""
        if driver is not None:
            driver.quit()

    def _wait_page_load(self, driver: WebDriver) -> None:
        """Wait for full page load (DOM + dynamic data)."""
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return jQuery.active == 0 if typeof jQuery != 'undefined' else True") 
                if "jQuery" in driver.page_source else True
            )
            
            time.sleep(2)
            
            logger.info("Page loaded completely")
        except TimeoutException:
            logger.warning("Timeout while waiting for page load")
            # Continue waiting anyway because elements may already be ready.
            time.sleep(3)

    def _wait_parser_html_with_beatutifulsoup(self, driver: WebDriver) -> BeautifulSoup:
        """Wait for page HTML to be ready for BeautifulSoup parsing."""
        html = BeautifulSoup(driver.page_source, "html.parser")

        # print(html.prettify())
        return html