import datetime
import logging
import queue
import re
import signal
import threading
import time
import tkinter as tk
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W
from tkinter.scrolledtext import ScrolledText

from selenium.common.exceptions import WebDriverException

from core.downloader import get_all_media, get_all_thumbnails, download_file
from core.kickstarter_service import get_project_info, get_creator_info
from core.notification.notification import NotificationManager
from core.page_scrap import PageScrap
from core.singlenton.app_path import AppPath
from core.singlenton.webdriver import WebDriver

logger = logging.getLogger(__name__)


class Clock(threading.Thread):
    """Class to display the time every seconds

    Every 5 seconds, the time is displayed using the logging.ERROR level
    to show that different colors are associated to the log levels
    """

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        logger.debug('kickstarter Scraping trying to connect with https://www.kickstarter.com/')
        previous = -1
        while not self._stop_event.is_set():
            now = datetime.datetime.now()
            if previous != now.second:
                time.sleep(0.2)

    def stop(self):
        self._stop_event.set()


class QueueHandler(logging.Handler):
    """Class to send logging records to a queue

    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """

    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=12)
        self.scrolled_text.grid(row=0, column=0, sticky=(N, S, W, E))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
                print(record)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


def process_url(url: str):
    routes = ['/description', '/faqs', '/posts', '/comments', '/community']
    for route in routes:
        url = url.replace(route, '')
    return url


def is_valid_url(url):
    # Regex to check valid URL
    regex = ("((http|https)://)(www.)?" +
             "[a-zA-Z0-9@:%._\\+~#?&//=]" +
             "{2,256}\\.[a-z]" +
             "{2,6}\\b([-a-zA-Z0-9@:%" +
             "._\\+~#?&//=]*)")

    # Compile the ReGex
    p = re.compile(regex)

    # If the string is empty
    # return false
    if url is None:
        return False

    # Return if the string
    # matched the ReGex
    if re.search(p, url):
        return True
    else:
        return False


def build_object_project(project):
    return {
        "name": project['name'],
        "blurb": project['blurb'],
        "goal": project['goal'],
        "pledged": project['pledged'],
        "state": project['state'],
        "slug": project['slug'],
        "disable_communication": project['disable_communication'],
        "country": project['country'],
        "country_displayable_name": project['country_displayable_name'],
        "currency": project['currency'],
        "currency_symbol": project['currency_symbol'],
        "currency_trailing_code": project['currency_trailing_code'],
        "deadline": project['deadline'],
        "state_changed_at": project['state_changed_at'],
        "created_at": project['created_at'],
        "launched_at": project['launched_at'],
        "staff_pick": project['staff_pick'],
        "is_starrable": project['is_starrable'],
        "backers_count": project['backers_count'],
        "static_usd_rate": project['static_usd_rate'],
        "usd_pledged": project['usd_pledged'],
        "converted_pledged_amount": project['converted_pledged_amount'],
        "fx_rate": project['fx_rate'],
        "current_currency": project['current_currency'],
        "usd_type": project['usd_type'],
    }


def get_project_id(url):
    project_id = process_url(url).split('?')[0].split('/')[-1]
    logger.info(project_id.upper())
    return project_id


def download_creator_info(project, path):
    logger.info("Downloading creator info")
    try:
        creator_api_url = project["creator"]["urls"]["api"]['user']
        creator = get_creator_info(creator_api_url)
        logger.info("Creator is " + creator["name"] + ", generating info...")
        creator_info = {
            "name": creator["name"],
            "profile": creator["urls"]["web"]["user"],
            "biography": creator["biography"],
            "links": PageScrap().get_creator_links()
        }
        logger.info("Downloading " + creator["name"] + " thumbnails...")
        get_all_thumbnails(creator['avatar'], path + 'creator\\avatar')
        logger.info("Thumbnails downloaded...")
        download_file(path + "creator\\", creator_info, "creator-info.txt")
        print(creator)
    except Exception as e:
        logger.error("Error getting creator info ->" + str(e))


def download_project_info(project_id, path):
    logger.info(msg='Searching project ' + project_id + 'info in Kickstarter')
    project_json = get_project_info(project_id)
    if project_json is not None and len(project_json['projects']) > 0:
        project = project_json['projects'][0]
        logging.info(msg='Download project info')
        download_file(path, build_object_project(project), "project-info.txt")
        logging.info(msg='Project info downloaded')
        logger.info('Searching project thumbnails...')
        get_all_thumbnails(project['photo'], path + 'video\\thumbnails')
        logger.info('Thumbnails downloaded')
        download_creator_info(project, path)
    else:
        logger.error('Kickstarter project not found')


class App:
    notification_manager = NotificationManager(background="white")
    workspace = AppPath()
    webdriver = WebDriver()
    scraper = PageScrap()

    def __init__(self, root):
        self.root = root
        root.title("Kickstarter Scrapper")
        root.iconbitmap("assets/favicon.ico")

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        # Create the panes and frames
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=1, column=0, sticky="nsew")
        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)
        console_frame = ttk.Labelframe(horizontal_pane, text="Output")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        horizontal_pane.add(console_frame, weight=1)
        third_frame = ttk.Labelframe(vertical_pane, text="Actions")
        vertical_pane.add(third_frame, weight=1)
        self.button = ttk.Button(third_frame, text='Download', command=lambda: self.fetch())
        self.button.grid(column=1, row=0, sticky=W)

        # Initialize all frames
        self.console = ConsoleUi(console_frame)
        self.clock = Clock()
        self.clock.start()
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def fetch(self):
        th = threading.Thread(target=self.download)
        th.start()

    def close(self):
        self.webdriver.quit()
        self.root.quit()

    def download(self):
        try:
            url = self.webdriver.current_url
            logger.info(url)
            if is_valid_url(url) and url.startswith("https://www.kickstarter.com/projects/"):
                project_id = get_project_id(url)
                path = self.get_project_path(project_id)
                self.button['state'] = tk.DISABLED
                self.button['text'] = 'Downloading...'
                logger.info('Starting web scraping for project ' + project_id)
                logger.info('Starting image scraping ')
                self.download_images(path)
                logger.info('Starting video scraping ')
                self.download_videos(path)
                download_project_info(project_id, path)
                logger.info('Download successfully ')
                self.button['state'] = tk.NORMAL
                self.button['text'] = 'Download'
                self.create_notification(5, 'Project downloaded successfully')
            else:
                logger.error('Invalid Kickstarter project url ')
        except Exception:
            logger.error(msg='Unable to connect with Chrome browser, please install')

    def download_images(self, path):
        logger.info(msg='Init project images download')
        images_content = PageScrap().get_all_images()
        try:
            if images_content is not None:
                logger.info(msg='Found ' + str(len(images_content)) + ' images, starting download')
                get_all_media(images_content, path, '', 'images')
                logger.info(msg='Project images downloaded successfully')
        except TypeError as e:
            logger.error('ERROR getting images from page -> ' + str(e))
        self.webdriver.execute_script("window.scrollTo(0,0)")

    def download_videos(self, path):
        logger.info(msg='Init project video download')
        videos = PageScrap().get_video_links()
        try:
            if videos is not None:
                logger.info(msg='Found ' + str(len(videos)) + ' videos, starting download')
                get_all_media(videos, path + 'video')
                logger.info(msg='Project videos downloaded successfully')
        except TypeError as e:
            logger.error('ERROR getting videos from page -> ' + str(e))
        self.webdriver.execute_script("window.scrollTo(0,0)")

    def get_project_path(self, project_id):
        path = self.workspace + '\\downloads\\' + project_id + '\\'
        logger.info('Project will save in ' + path)
        return path

    def create_notification(self, start_time, text):
        def notify():
            def builder(interior):
                tk.Label(interior, text=text, background="white").pack()

            self.notification_manager.create_notification(builder=builder)

        self.root.after(start_time, notify)

    def quit(self):
        self.clock.stop()
        self.root.destroy()


def main():
    logging.basicConfig(level=logging.DEBUG)
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()


if __name__ == '__main__':
    main()
