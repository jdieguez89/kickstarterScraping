import time
from urllib.parse import urlparse

import requests
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from core.singlenton.logger import Logger
from core.singlenton.webdriver import WebDriver


class PageScrap:

    def __init__(self):
        self.logging = Logger()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/50.0.2661.102 Safari/537.36'}

        self.driver = WebDriver()

    def get_video_links(self):
        try:
            videos = self.driver.find_elements_by_tag_name('source')
            urls = [img.get_attribute('src') for img in videos]
            return urls
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            self.logging.info(msg='Unable to connect..., check your connection and try again')
            self.logging.error(msg=str(e))
            raise SystemExit(e)

    def is_valid(self, url):
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_all_images(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rte__content")))
            images = self.driver.find_elements_by_tag_name('img')

            for i in images:
                self.driver.execute_script("arguments[0].scrollIntoView();", i)
                time.sleep(2)

            time.sleep(10)
            img_tags = self.driver.find_elements_by_tag_name('img')
            urls = [img.get_attribute('src') for img in img_tags]
            return urls
        except TimeoutException as e:
            self.logging.info('TimeoutException ' + e.msg)
            return ValueError
        except WebDriverException as e:
            self.logging.info('WebDriverException ' + e.msg)
            return ValueError
