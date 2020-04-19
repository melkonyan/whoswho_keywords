import aiohttp
from aiohttp_retry import RetryClient
import asyncio
import os
import re

class Downloader(object):

    def __init__(self):
        self.cache_dir = None

    def register_options(self, argparser):
        argparser.add_argument('--cache', dest='downloader_cache_dir', default='cache',
                                help='Path to the folder where downloaded urls will be cached. To disable cache, delete the folder.')

    def create_session(self):
        return RetryClient()

    def prepare_cache(self, args):
        self.cache_dir = args.downloader_cache_dir
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

    def use_cache(self):
        return self.cache_dir is not None

    def cache_key(self, url):
        assert self.use_cache()
        return os.path.join(self.cache_dir, re.escape(url).replace('/','\\'))

    def has_cache(self, url):
        return self.use_cache() and os.path.exists(self.cache_key(url))

    def get_cache(self, url):
        with open(self.cache_key(url), 'r') as url_cache:
            return url_cache.read()

    def put_cache(self, url, contents):
        with open(self.cache_key(url), 'w') as url_cache:
            url_cache.write(contents)

    async def try_to_download(self, session, url):
        async with session.get(url, retry_attempts=3) as res:
            if res.status is not 200:
                print('Error fetching {}, staus={}'.format(url, res.status))
            return await res.text()


    async def download(self, session, url, result_queue):
        first_try = True
        for _ in range(2):
            try:
                contents = await self.try_to_download(session, url)
                if self.use_cache():
                    self.put_cache(url, contents)
                await result_queue.put((url, contents))
            except aiohttp.ServerDisconnectedError:
                if not first_try:
                    print('Failed to download {}. Repeated server disconnected error'.format(url))
                    await result_queue.put((url, None))
                    return
                first_try = False
                print('Server disconnected, we might have hit a crawler blocker. Sleep and try again.')
                await asyncio.sleep(10)

    async def download_or_cache(self, session, url, result_queue):
        if self.has_cache(url):
            print('Found cache entry for {}'.format(url))
            await result_queue.put((url, self.get_cache(url)))
            return
        print('Downloading {}'.format(url))
        await self.download(session, url, result_queue)

    async def download_all(self, urls, consumer_fn):
        results_queue = asyncio.Queue()
        async with self.create_session() as download_session:
            downloaders = [asyncio.create_task(self.download_or_cache(download_session, url, results_queue)) for url in urls]
            consumer = asyncio.create_task(consumer_fn(results_queue))
            await asyncio.gather(*downloaders)
            await results_queue.join()
            consumer.cancel()
