import os
from selenium import webdriver


class AppPath:
    class __AppPath:
        def __init__(self):
            self.path = os.path.abspath(os.getcwd())

    path = None

    def __new__(cls):
        if not AppPath.path:
            AppPath.path = AppPath.__AppPath().path
        return AppPath.path
