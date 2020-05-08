import unittest
import asyncio
import shutil
import os
from datetime import datetime, timedelta

from downloader import Downloader


class RequestStub:

    def __init__(self, page):
        self.page = page
        self.status = 200

    async def text(self):
        return self.page

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass


class HttpClientStub():

    fake_pages = {
        'url1': 'page1',
        'url2': 'page2',
        'url3': 'page3',
    }

    def __init__(self):
        self.calls = []

    def get_data(self):
        return self.fake_pages

    def get_calls(self):
        return self.calls

    def get(self, url, **kwargs):
        self.calls.append(url)
        return RequestStub(self.fake_pages.get(url, None))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

class ConsumerStub:

    def __init__(self):
        self.data = {}

    async def __call__(self, url, page):
        self.data[url] = page

    def get_data(self):
        return self.data

class ArgsStub:

    downloader_cache_dir = 'test_cache'
    qps = 10

class DownloaderTest(unittest.TestCase):

    def test_download_all(self):
        http_client = HttpClientStub()
        downloader = Downloader(http_client_factory=lambda : http_client)
        downloader.prepare(ArgsStub())
        consumer = ConsumerStub()
        cache_consumer = ConsumerStub()
        urls = list(http_client.get_data().keys())

        asyncio.run(downloader.download_all(urls, consumer))
        asyncio.run(downloader.download_all(urls, cache_consumer))

        # Verify that all pages were downloaded
        self.assertEqual(consumer.get_data(), http_client.get_data())
        self.assertEqual(http_client.get_calls(), urls)

        # Verify that no more pages were downloaded
        self.assertEqual(cache_consumer.get_data(), http_client.get_data())
        self.assertEqual(http_client.get_calls(), urls)

    def test_qps(self):
        http_client = HttpClientStub()
        downloader = Downloader(http_client_factory=lambda: http_client)
        args = ArgsStub()
        args.qps = 1
        downloader.prepare(args)
        consumer = ConsumerStub()
        urls = list(http_client.get_data().keys())

        start = datetime.now()
        asyncio.run(downloader.download_all(urls, consumer))
        end = datetime.now()

        # Verify that at qps = 1, we spent ~1 sec per download
        delta = timedelta(microseconds=500000)
        expected_duration = timedelta(seconds=len(urls)-1)
        actual_duration = end - start
        self.assertLess(actual_duration, expected_duration + delta)
        self.assertGreater(actual_duration, expected_duration - delta)


    def tearDown(self):
        if os.path.exists(ArgsStub.downloader_cache_dir):
            shutil.rmtree(ArgsStub.downloader_cache_dir)

if __name__ == '__main__':
    unittest.main()
