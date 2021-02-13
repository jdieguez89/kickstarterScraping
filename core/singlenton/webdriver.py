import os

from selenium import webdriver

from core.singlenton.app_path import AppPath
from core.singlenton.logger import Logger


class WebDriver:
    class __WebDriver:
        def __init__(self):
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--start-maximized")
            # self.options.add_argument("--headless")
            # self.options.headless = True
            self.driver_path = os.path.abspath(AppPath.path + '//driver//chromedriver.exe')
            self.driver = webdriver.Chrome(executable_path=self.driver_path, chrome_options=self.options)
            self.driver.get('https://www.kickstarter.com/')

    def close_webdriver(self):
        print('close chrome')
        self.driver.quit()

    driver = None

    def __new__(cls):
        if not WebDriver.driver:
            try:
                WebDriver.driver = WebDriver.__WebDriver().driver
            except Exception as e:
                Logger().error('ERROR Starting webdriver')
                Logger().error(str(e))

        return WebDriver.driver
