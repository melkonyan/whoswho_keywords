import json
import argparse
import math
import asyncio
from lxml import html
from downloader import Downloader


class WhoswhoCrawler(object):

    URL_PATTERN = 'http://whoswho.senescence.info/people.php?page={}'
    RESEARCHERS_PER_PAGE = 50

    def __init__(self, downloader=Downloader()):
        self.downloader=downloader

    def register_options(self, argparser):
        self.downloader.register_options(argparser)

    async def parse(self, result_queue):
        while True:
            url, contents = await result_queue.get()
            print('Parsing {}'.format(url))
            if contents is None:
                continue
            html_tree = html.fromstring(contents)
            self.researchers_per_url[url] = html_tree.xpath('//*[@id="content"]/div/div[2]/ul/li/h2/a/text()')
            result_queue.task_done()

    async def crawl(self, args, num_researchers):
        self.researchers_per_url = {}
        self.downloader.prepare_cache(args)
        num_pages = int(math.ceil(num_researchers / self.RESEARCHERS_PER_PAGE))
        page_urls = [self.URL_PATTERN.format(page_num) for page_num in range(1, num_pages+1)]
        await self.downloader.download_all(page_urls, self.parse)
        researchers_info = {
            page_num*self.RESEARCHERS_PER_PAGE + id: name
            for page_num, url in enumerate(page_urls)
            for id, name in enumerate(self.researchers_per_url[url])
            }
        print('Parsed {} researchers'.format(len(researchers_info)))
        return researchers_info





async def main():
    crawler = WhoswhoCrawler()
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--out', dest='output', help='Path to the json output file', default='researchers.json')
    parser.add_argument('--num', type=int, dest='num_researchers', help='How many researchers to download', default=50)
    crawler.register_options(parser)
    args = parser.parse_args()
    researchers = await crawler.crawl(args, args.num_researchers)
    with open(args.output, 'w') as output:
        json.dump(researchers, output)

if __name__ == '__main__':
    asyncio.run(main())
