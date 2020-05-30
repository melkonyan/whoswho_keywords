import json
import argparse
import asyncio
import os
import logging
from lxml import html
from downloader import Downloader
import xmltodict
import traceback
from tqdm import tqdm

LOGS_DIR = 'logs'
LOG_FILE = 'logs/pubmed.log'
PAPER_LIST_URL_PATTERN = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=github.com/melkonyan/whoswho_keywords&email=sasha.melkonyan+crawler@gmail.com&retmax=300&term={name}%20{surname}%20aging&format=json&{api_key}'
PAPER_DETAILS_URL_PATTERN = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={id}&tool=github.com/melkonyan/whoswho_keywords&email=sasha.melkonyan+crawler@gmail.com&format=xml&{api_key}'


def setup_logging():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    with open(LOG_FILE, 'w'): pass
    logging.basicConfig(filename=LOG_FILE, filemode='w', level=logging.INFO)

class PubmedCrawler(object):

    def __init__(self, downloader=Downloader()):
        self.downloader = Downloader()

    def register_options(self, argparser):
        argparser.add_argument('--no-details', dest='fetch_details', action='store_false', help='Only parse list of paper ids for each researcher, dont download each paper contents.', default=True)
        argparser.add_argument('--api_key', help='Pubmed API key. For more details on how to get one, see https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities', default=None)
        self.downloader.register_options(argparser)

    def prepare(self, args):
        self.api_key = args.api_key
        self.fetch_details = args.fetch_details
        self.downloader.prepare(args)

    def format_name(self, name):
        surname, name = name.split(', ')
        return {'surname': surname, 'name': name}

    def format_api_key(self):
        return 'api_key='+self.api_key if self.api_key else ''

    async def parse_details(self, url, contents):
        if contents is None:
            return
        try:
            d = xmltodict.parse(contents)
            paper_id = d['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['PMID']['#text']
            researcher_id = self.researcher_id_for_paper[paper_id]
            self.papers[researcher_id]['papers'][paper_id] = d
        except Exception as ex:
            print('Failed to parse url {}'.format(url))
            traceback.print_exc()

    async def parse_papers(self, url, contents):
        if contents is None:
            return
        print('Parsing {}'.format(url))
        try:
            researcher_id = self.researcher_id_for_url[url]
            paper_ids = json.loads(contents).get('esearchresult', {}).get('idlist', [])
            self.papers[researcher_id]['paper_ids'] = paper_ids
            print('Done parsing')
        except Exception as ex:
            print('Failed to parse {}'.format(url))
            traceback.print_exc()

    async def crawl_paper_details(self):
        print(list(self.papers.values())[0]['paper_ids'])
        total_num_papers = sum([len(papers['paper_ids']) for papers in self.papers.values()])
        progress = tqdm(total=total_num_papers)
        num_crawled = 0
        for researcher_id, papers in self.papers.items():
            paper_ids = papers['paper_ids']
            paper_details_url = [PAPER_DETAILS_URL_PATTERN.format(
                api_key = self.format_api_key(),
                id = id) for id in paper_ids
            ]
            for id in paper_ids:
                self.researcher_id_for_paper[id] = researcher_id
            await self.downloader.download_all(paper_details_url, self.parse_details)
            num_crawled += len(paper_ids)
            progress.update(len(paper_ids))
        progress.close()

    async def crawl(self, researchers):
        paper_urls = {id: PAPER_LIST_URL_PATTERN.format(
            api_key=self.format_api_key(), **self.format_name(name))
            for id, name in list(researchers.items())}
        self.papers = {
            id: {'researcher': researchers[id], 'papers': {}, 'paper_ids': []}
            for id, url in paper_urls.items()
        }
        self.researcher_id_for_url = {url: id for id, url in paper_urls.items()}
        self.researcher_id_for_paper = {}
        await self.downloader.download_all(paper_urls.values(), self.parse_papers)
        if self.fetch_details:
            await self.crawl_paper_details()
        print('Done')
        return self.papers


async def main():
    crawler = PubmedCrawler()
    parser = argparse.ArgumentParser(description='Download pubmed paper titles for a set of researchers')
    parser.add_argument('--in', dest='input', help='Path to a json file containing researchers whose papers should be downloaded', default='researchers.json')
    parser.add_argument('--out', dest='output', help='Path to a json file where to store crawled papers', default='papers.json')
    crawler.register_options(parser)
    args = parser.parse_args()
    crawler.prepare(args)   
    setup_logging()
    with open(args.input, 'r') as input, open(args.output, 'w') as output:
        researchers = json.load(input)
        papers = await crawler.crawl(researchers)
        json.dump(papers, output, )

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
