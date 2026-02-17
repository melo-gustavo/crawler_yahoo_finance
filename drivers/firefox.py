from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from drivers.base_driver import BaseDriver


class Firefox:
    def start(self, headless: bool = False) -> WebDriver:
        options = webdriver.FirefoxOptions()
        BaseDriver().set_config_driver(options, headless=headless)

        driver = webdriver.Firefox(options=options)
        return driver
