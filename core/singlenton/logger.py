import logging
try:
    from cStringIO import StringIO      # Python 2
except ImportError:
    from io import StringIO


class Logger:
    class __Logger:
        def __init__(self):
            logging.basicConfig(filename='downloader.log', level=logging.DEBUG, format='%(asctime)s %(message)s',
                                datefmt='%d/%m/%Y %H:%M:%S')
            logging.info(msg='Opening downloader')

        def critical(self, msg):
            logging.critical(msg)

        def error(self, msg):
            logging.error(msg)

        def warn(self, msg):
            logging.warning(msg)

        def info(self, msg):
            logging.info(msg)

        def debug(self, msg):
            logging.debug(msg)

    instance = None

    def __new__(cls):
        if not Logger.instance:
            Logger.instance = Logger.__Logger()
        return Logger.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, instance, name):
        return setattr(self, instance, name)
