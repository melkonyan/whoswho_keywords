import json
import argparse
import asyncio
from lxml import html
from downloader import Downloader



URL_PATTERN = 'https://www.ncbi.nlm.nih.gov/pubmed?cmd=search&term={}+aging'

class PubmedCrawler(object):

    def __init__(self, downloader=Downloader()):
        self.downloader = Downloader()

    def register_options(self, argparser):
        self.downloader.register_options(argparser)

    def format_name(self, name):
        surname, name = name.split(', ')
        return '{}-{}'.format(surname, name[0])

    async def parse(self, result_queue):
        while True:
            url, contents = await result_queue.get()
            if contents is None:
                continue
            print('Parsing {}'.format(url))
            html_tree = html.fromstring(contents.encode('utf-8'))
            titles = [el.text_content() for el in html_tree.xpath('//*[@id="maincontent"]/div/div[5]/div/div[2]/p/a')]
            self.papers_per_url[url] = titles
            result_queue.task_done()


    async def crawl(self, researchers, args):
        self.downloader.prepare_cache(args)
        self.papers_per_url = {}
        paper_urls = {id: URL_PATTERN.format(self.format_name(name)) for id, name in list(researchers.items())}
        await self.downloader.download_all(paper_urls.values(), self.parse)
        papers = {id:
            {'researcher': researchers[id], 'papers': self.papers_per_url[url]}
            for id, url in paper_urls.items() if url in self.papers_per_url.keys()}
        print('Successfully crawled papers for {} out of {} researchers'.format(len(researchers), len(papers)))
        return papers


async def main():
    crawler = PubmedCrawler()
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--in', dest='input', help='Path to the input json file', default='researchers.json')
    parser.add_argument('--out', dest='output', help='Path to the json output file', default='papers.json')
    crawler.register_options(parser)
    args = parser.parse_args()
    # TODO: figure out how to print special charaters properly (e.g. beta)
    with open(args.input, 'r') as input, open(args.output, 'w') as output:
        researchers = json.load(input)
        papers = await crawler.crawl(researchers, args)
        json.dump(papers, output, )

if __name__ == '__main__':
    asyncio.run(main())
