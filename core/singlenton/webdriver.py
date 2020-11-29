import os
from selenium import webdriver

from core.singlenton.app_path import AppPath


class WebDriver:
    class __WebDriver:
        def __init__(self):
            self.driver_path = AppPath() + '/driver/chromedriver.exe'
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(executable_path=self.driver_path, chrome_options=self.options)

    def close_webdriver(self):
        self.driver.quit()

    driver = None

    def __new__(cls):
        if not WebDriver.driver:
            WebDriver.driver = WebDriver.__WebDriver().driver
        return WebDriver.driver
