import aiohttp
from aiohttp_retry import RetryClient
import asyncio
import os
import re
import heapq
from datetime import datetime, timedelta

MAX_FILE_NAME_LEN = 250
ONE_SEC = timedelta(seconds=1)

class DefaultArgs:
    qps = 100
    downloader_cache_dir = 'cache'

class DownloadHistory:

    def __init__(self):
        self.records = []

    def oldest_record(self):
        return self.records[0]

    def remote_old_records(self, t: datetime):
        while len(self.records) > 0 and self.oldest_record() < t:
            heapq.heappop(self.records)

    def add_record(self, t: datetime):
        heapq.heappush(self.records, t)

    def __len__(self):
        return len(self.records)

class Downloader(object):

    def __init__(self, http_client_factory = RetryClient):
        self.cache_dir = None
        self.download_paused = False
        self.http_client_factory = http_client_factory
        self.prepare(DefaultArgs())
        self.args_registered = False
        self.download_history = DownloadHistory()
        self.semaphore = None

    def register_options(self, argparser):
        argparser.add_argument('--cache', dest='downloader_cache_dir', default=DefaultArgs.downloader_cache_dir,
                                help='Path to the folder where downloaded urls will be cached. To disable cache, delete the folder.')
        argparser.add_argument('--qps', type=int, default=DefaultArgs.qps, help='Limit the number of concurrent requests sent to the server')

    def create_session(self):
        return self.http_client_factory()

    def prepare(self, args):
        self.qps = args.qps
        self.cache_dir = args.downloader_cache_dir
        self.max_url_len = MAX_FILE_NAME_LEN - len(self.cache_dir)
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
        self.args_registered = True

    def use_cache(self):
        return self.cache_dir is not None

    def cache_key(self, url):
        assert self.use_cache()
        url = re.escape(url).replace('/','\\')
        if len(url) > self.max_url_len:
            url = url[len(url)-self.max_url_len:]
        return os.path.join(self.cache_dir, url)

    def has_cache(self, url):
        return self.use_cache() and os.path.exists(self.cache_key(url))

    def get_cache(self, url):
        with open(self.cache_key(url), 'r') as url_cache:
            return url_cache.read()

    def put_cache(self, url, contents):
        with open(self.cache_key(url), 'w') as url_cache:
            url_cache.write(contents)

    async def try_to_download(self, session, url):
        async with self.semaphore:
            curr_time = datetime.now()
            self.download_history.remote_old_records(curr_time-ONE_SEC)
            if len(self.download_history) >= self.qps:
                sleep_time = self.download_history.oldest_record() + ONE_SEC - curr_time
                await asyncio.sleep(sleep_time.total_seconds())
            self.download_history.add_record(datetime.now())
            print('Downloading {}'.format(url))
            async with session.get(url, retry_attempts=2) as res:
                if res.status == 429:
                    print('Service returned status 429, trying to recover. Consider adjusting download throttle')
                    self.download_paused = True
                    await asyncio.sleep(10)
                    self.download_paused = False
                    return await self.try_to_download(session, url)
                elif not res.status == 200:
                    print('Error fetching {}, staus={}'.format(url, res.status))
                    return None
                return await res.text()


    async def download(self, session, url, result_queue):
        try:
            contents = await self.try_to_download(session, url)
            if self.use_cache():
                self.put_cache(url, contents)
            print('Download finished for {}'.format(url))
            await result_queue.put((url, contents))
        except aiohttp.ServerDisconnectedError as err:
            print('Failed to download {}. Repeated server disconnected error'.format(url))
            await result_queue.put((url, None))

    async def download_or_cache(self, session, url, result_queue):
        if self.has_cache(url):
            print('Found cache entry for {}'.format(url))
            await result_queue.put((url, self.get_cache(url)))
            return
        await self.download(session, url, result_queue)

    async def download_all(self, urls, callback):
        """
        asynchronously downloads urls from the given list and forwars results to
        the callback function

        @param consumer_fn function accepting two parameters: url and the
            downloaded page.
        """
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.qps)
        if not self.args_registered:
            print('Warning: Downloader.prepare was not called')
        results_queue = asyncio.Queue()

        async def consumer():
            while True:
                url, page = await results_queue.get()
                await callback(url, page)
                results_queue.task_done()

        async with self.create_session() as download_session:
            downloaders = [asyncio.create_task(self.download_or_cache(download_session, url, results_queue)) for url in urls]
            consumer_task = asyncio.create_task(consumer())
            await asyncio.gather(*downloaders)
            await results_queue.join()
            consumer_task.cancel()
