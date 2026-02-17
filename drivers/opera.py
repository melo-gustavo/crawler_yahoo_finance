from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from drivers.base_driver import BaseDriver


class Opera:
    def start(self, headless: bool = False) -> WebDriver:
        options = webdriver.ChromeOptions()
        BaseDriver().set_config_driver(options, headless=headless)

        driver = webdriver.Chrome(options=options)
        return driver
