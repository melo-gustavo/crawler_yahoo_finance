from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class Firefox:
    def start(self) -> WebDriver:
        driver = webdriver.Firefox()
        driver.implicitly_wait(5)
        return driver
