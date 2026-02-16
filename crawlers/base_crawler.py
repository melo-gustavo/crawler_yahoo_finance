from fastapi import Request
from selenium.webdriver.remote.webdriver import WebDriver

from drivers.edge import Edge
from drivers.firefox import Firefox
from drivers.google_chrome import GoogleChrome
from drivers.opera import Opera
from drivers.safari import Safari
from utils.utils import detect_browser


class BaseCrawler:
    def _start_session(self, request: Request) -> tuple[WebDriver, str]:
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
        driver = selected_browser.start()
        return driver, browser

    def _finish_session(self, driver: WebDriver | None) -> None:
        """Always close browser session, even if the crawl fails."""
        if driver is not None:
            driver.quit()
