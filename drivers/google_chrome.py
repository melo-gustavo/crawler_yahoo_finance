from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class GoogleChrome:
    def start(self) -> WebDriver:
        driver = webdriver.Chrome()
        driver.implicitly_wait(5)
        return driver
