import json
import argparse
import asyncio
from lxml import html
from downloader import Downloader



URL_PATTERN = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=github.com/melkonyan/whoswho_keywords&email=sasha.melkonyan+crawler@gmail.com&retmax=300&term={name}%20{surname}%20aging&format=json&{api_key}'

class PubmedCrawler(object):

    def __init__(self, downloader=Downloader()):
        self.downloader = Downloader()

    def register_options(self, argparser):
        argparser.add_argument('--api_key', help='', default=None)
        self.downloader.register_options(argparser)

    def format_name(self, name):
        surname, name = name.split(', ')
        return {'surname': surname, 'name': name}

    async def parse(self, url, contents):
        if contents is None:
            return
        print('Parsing {}'.format(url))
        try:
            paper_ids = json.loads(contents).get('esearchresult', {}).get('idlist', [])
            print('Done parsing')
            self.papers_per_url[url] = paper_ids
        except Exception as ex:
            print('Failed to parse {}'.format(url))
            self.papers_per_url[url] = []

    async def crawl(self, researchers, args):
        self.api_key = args.api_key
        self.downloader.prepare(args)
        self.papers_per_url = {}
        paper_urls = {id: URL_PATTERN.format(
            api_key='api_key='+self.api_key if self.api_key else '', **self.format_name(name))
            for id, name in list(researchers.items())}
        await self.downloader.download_all(paper_urls.values(), self.parse)
        papers = {id:
            {'researcher': researchers[id], 'papers': self.papers_per_url[url]}
            for id, url in paper_urls.items() if url in self.papers_per_url.keys()}
        print('Successfully crawled papers for {} out of {} researchers'.format(len(researchers), len(papers)))
        return papers


async def main():
    crawler = PubmedCrawler()
    parser = argparse.ArgumentParser(description='Download pubmed paper titles for a set of researchers')
    parser.add_argument('--in', dest='input', help='Path to a json file containing researchers whose papers should be downloaded', default='researchers.json')
    parser.add_argument('--out', dest='output', help='Path to a json file where to store crawled papers', default='papers.json')
    crawler.register_options(parser)
    args = parser.parse_args()
    with open(args.input, 'r') as input, open(args.output, 'w') as output:
        researchers = json.load(input)
        papers = await crawler.crawl(researchers, args)
        json.dump(papers, output, )

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
