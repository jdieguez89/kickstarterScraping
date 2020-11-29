import logging
import os
import threading
from queue import Queue

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3 import Retry

""" Improve this"""


def get_ext(url):
    """Return the filename extension from url, or ''."""
    ext = str(url).split('?')[0]
    file = ext.split('.')[-1]
    return file


def get_all_media(files, path, version='', media_type=''):
    input_queue = Queue()
    result_hash = {}
    cache = {}

    class DownloadFileThread(threading.Thread):
        def __init__(self, input_queue, result_hash):
            super().__init__()
            self.input_queue = input_queue
            self.result_hash = result_hash

        def run(self):
            while True:
                file_queue = self.input_queue.get()
                download(file_queue, path, version, media_type)
                self.input_queue.task_done()

    # Start 20 Threads, all are waiting in run -> self.input_queue.get()
    for i in files:
        thread = DownloadFileThread(input_queue, result_hash)
        thread.setDaemon(True)
        thread.start()

    # Fill the input queue
    for file in files:
        input_queue.put(file)

    input_queue.join()
    cache.update(result_hash)
    return result_hash


def get_all_thumbnails(thumbnails, path):
    input_queue = Queue()
    result_hash = {}
    cache = {}

    class DownloadThumbnailsThread(threading.Thread):
        def __init__(self, input_queue, result_hash):
            super().__init__()
            self.input_queue = input_queue
            self.result_hash = result_hash

        def run(self):
            while True:
                thumbnail_queue = self.input_queue.get()
                download(url=thumbnail_queue[1],
                         pathname=path + '\\' + thumbnail_queue[0])
                self.input_queue.task_done()

    # Start 20 Threads, all are waiting in run -> self.input_queue.get()
    for i in thumbnails:
        thread = DownloadThumbnailsThread(input_queue, result_hash)
        thread.setDaemon(True)
        thread.start()

    # Fill the input queue
    for thumbnail in thumbnails:
        if thumbnail != 'key':
            input_queue.put([thumbnail, thumbnails[thumbnail]])

    input_queue.join()
    cache.update(result_hash)
    return result_hash


def download(url, pathname, version='', media_type=''):
    """
    Downloads a file given an URL and puts it in the folder `pathname`
    """

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/50.0.2661.102 Safari/537.36'}

    # if media type is images then separate each one by extension
    if media_type == 'images':
        pathname += '\\images\\' + get_ext(url)

    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname, exist_ok=True)
    # download the body of response by chunk, not immediately
    response = session.get(url, headers=headers)

    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))

    # get the file name
    filename = os.path.join(pathname, resolve_file_name(url))

    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024),
                    f"Downloading {resolve_file_name(url)} version {version}", total=file_size, unit="B",
                    unit_scale=True, unit_divisor=1024)

    with open(filename, "wb") as f:
        for data in progress:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))
    logging.info(msg='Saved in ' + pathname)


def get_ext(url):
    """Return the filename extension from url, or ''."""
    ext = str(url).split('?')[0]
    file = ext.split('.')[-1]
    return file


def resolve_file_name(url):
    return str(url).split('?')[0].split("/")[-1]
