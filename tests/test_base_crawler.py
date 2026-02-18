from unittest.mock import Mock, patch

from crawlers.base_crawler import BaseCrawler


def test_finish_session_calls_quit_when_driver_exists():
    crawler = BaseCrawler()
    driver = Mock()

    crawler._finish_session(driver)

    driver.quit.assert_called_once()


def test_finish_session_no_driver_is_safe():
    crawler = BaseCrawler()

    crawler._finish_session(None)


def test_start_session_passes_headless_to_driver_start():
    crawler = BaseCrawler()
    request = Mock()
    request.headers = {"user-agent": "dummy"}

    browser_instance = Mock()
    browser_instance.start.return_value = "driver-instance"

    with (
        patch("crawlers.base_crawler.detect_browser", return_value="Chrome"),
        patch("crawlers.base_crawler.GoogleChrome", return_value=browser_instance),
    ):
        driver, browser = crawler._start_session(request, headless=True)

    assert driver == "driver-instance"
    assert browser == "Chrome"
    browser_instance.start.assert_called_once_with(headless=True)


def test_wait_parser_html_with_beautifulsoup_returns_soup():
    crawler = BaseCrawler()
    driver = Mock()
    driver.page_source = "<html><body><table><tr><td>ok</td></tr></table></body></html>"

    soup = crawler._wait_parser_html_with_beatutifulsoup(driver)

    assert soup.select_one("table") is not None
