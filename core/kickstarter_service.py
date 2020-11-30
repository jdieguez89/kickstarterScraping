import logging

import requests

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_project_info(project):
    try:
        return requests.get('https://www.kickstarter.com/projects/search.json?search=&term=' + project).json()
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.error(msg='Unable to connect..., check your connection and try again')
        pass


def get_creator_info(url):
    try:
        return requests.get(url).json()
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logger.error(msg='Unable to connect..., check your connection and try again')
        pass
