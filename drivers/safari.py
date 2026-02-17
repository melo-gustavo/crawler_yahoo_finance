from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from drivers.base_driver import BaseDriver


class Safari:
    def start(self, headless: bool = False) -> WebDriver:
        options = webdriver.SafariOptions()
        BaseDriver().set_config_driver(options, headless=headless)

        driver = webdriver.Safari(options=options)
        return driver
