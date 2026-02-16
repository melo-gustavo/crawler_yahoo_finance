from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class Safari:
    def start(self) -> WebDriver:
        driver = webdriver.Safari()
        driver.implicitly_wait(5)
        return driver
