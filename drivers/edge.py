from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from drivers.base_driver import BaseDriver


class Edge:
    def start(self, headless: bool = False) -> WebDriver:
        options = webdriver.EdgeOptions()
        BaseDriver().set_config_driver(options, headless=headless)

        driver = webdriver.Edge(options=options)
        return driver
