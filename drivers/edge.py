from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class Edge:
    def start(self) -> WebDriver:
        driver = webdriver.Edge()
        driver.implicitly_wait(5)
        return driver
