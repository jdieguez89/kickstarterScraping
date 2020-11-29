import requests

from core.singlenton.logger import Logger


class KickstarterService:
    logging = Logger()

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    def get_project_info(self, project):
        try:
            self.logging.info(msg='https://www.kickstarter.com/projects/search.json?search=&term=' + project)
            return requests.get('https://www.kickstarter.com/projects/search.json?search=&term=' + project).json()
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            self.logging.info(msg='Unable to connect..., check your connection and try again')
            pass
