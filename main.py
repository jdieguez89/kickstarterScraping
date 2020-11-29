import tkinter as tk
from tkinter.ttk import Progressbar

from core.downloader import download, get_all_media, get_all_thumbnails
from core.kickstarter_service import KickstarterService
from core.notification.notification import NotificationManager
from core.page_scrap import PageScrap
from core.singlenton.app_path import AppPath
from core.singlenton.logger import Logger
from core.singlenton.webdriver import WebDriver


def make_form(root, fields):
    entries = []
    for field in fields:
        row = tk.Frame(root)
        lab = tk.Label(row, width=15, text=field, anchor='w')
        ent = tk.Entry(row)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=10)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries.append((field, ent))
    return entries


def process_url(url: str):
    routes = ['/description', '/faqs', '/posts', '/comments', '/community']
    for route in routes:
        url = url.replace(route, '')
    return url


class App:
    notification_manager = NotificationManager(background="white")
    logging = Logger()
    workspace = AppPath()
    scraper = PageScrap()
    root = tk.Tk()
    root.geometry("800x100")
    root.title("Kickstarter Scrapper")
    # root.iconbitmap("assets/favicon.ico")
    fields = ['Kickstarter url']
    webdriver = WebDriver()

    def __init__(self):
        print('Init application:' + self.workspace)
        self.progress = Progressbar(self.root, orient=tk.HORIZONTAL, length=100, mode='determinate')

    def update_progress(self, value):
        print('updating progress')
        num = ((value['value'] / value['total']) * 100).__round__(0)
        self.progress.step(num)

    def fetch(self, entries):
        url = entries[0][1].get()

        if url != '':
            self.download(url)

    def close(self):
        self.webdriver.quit()
        self.root.quit()

    def download(self, url):
        project_id = self.get_project_id(url)
        path = self.get_project_path(project_id)
        self.download_project_info(project_id, path)
        self.logging.info('Starting web scraping for project ' + project_id)
        self.webdriver.get(url)
        self.download_images(path)
        self.download_videos(path)

    def download_project_info(self, project_id, path):
        self.logging.info(msg='Searching project ' + project_id + 'info in Kickstarter')
        project_json = KickstarterService().get_project_info(project_id)
        if project_json is not None and len(project_json['projects']) > 0:
            project = project_json['projects'][0]
            # logging.info(msg='Download project info')
            # export_project_info = DownloadFiles().download_file(path=path, info=self.build_object_project(project))
            # if export_project_info:
            #     logging.info(msg='Project info exported as json in ' + path)
            get_all_thumbnails(project['photo'], path + 'video\\thumbnails')

    def download_images(self, path):
        self.logging.info(msg='Init webpage images download')
        images_content = PageScrap().get_all_images()
        try:
            if images_content is not None:
                self.logging.info(msg='Found ' + str(len(images_content)) + ' images')
                get_all_media(images_content, path, '', 'images')
                self.logging.info(msg='Webpage images downloaded successfully')
        except TypeError as e:
            self.logging.error('ERROR getting images from page -> ' + str(e))
        self.webdriver.execute_script("window.scrollTo(0,0)")

    def download_videos(self, path):
        self.logging.info(msg='Init webpage video download')
        videos = PageScrap().get_video_links()
        try:
            if videos is not None:
                self.logging.info(msg='Found ' + str(len(videos)) + ' videos')
                get_all_media(videos, path + 'video')
                self.logging.info(msg='Webpage videos downloaded successfully')
        except TypeError as e:
            self.logging.error('ERROR getting videos from page -> ' + str(e))
        self.webdriver.execute_script("window.scrollTo(0,0)")

    def get_project_id(self, url):
        project_id = process_url(url).split('?')[0].split('/')[-1]
        self.logging.info(
            msg='***************************** ' + project_id.upper() + '***************************** ')
        return project_id

    def get_project_path(self, project_id):
        return self.workspace + '\\downloads\\' + project_id + '\\'

    def create_notification(self, start_time, text):
        def notify():
            def builder(interior):
                tk.Label(interior, text=text, background="white").pack()

            self.notification_manager.create_notification(builder=builder)

        self.root.after(start_time, notify)

    def init_app(self):
        ents = make_form(self.root, self.fields)
        self.root.bind('<Return>', (lambda event, e=ents: self.fetch(e)))
        # self.progress.pack(pady=15)
        # self.progress.place(x=10, y=90, width=380)

        b2 = tk.Button(self.root, text='Quit', command=(lambda e=ents: self.close()))
        b1 = tk.Button(self.root, text='Download', command=(lambda e=ents: self.fetch(e)), bg='brown', fg='white')
        b1.pack(side=tk.RIGHT, padx=10, pady=5)
        b2.pack(side=tk.RIGHT, padx=10, pady=5)

        self.root.mainloop()


if __name__ == '__main__':
    App().init_app()
