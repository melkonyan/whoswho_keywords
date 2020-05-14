import json
import argparse
import nltk
import itertools
from nltk.probability import FreqDist

from tokenizer import Tokenizer
from pubmed_processor import PubmedProcessor


class KeywordsFinder(object):

    def register_options(self, argparser):
        argparser.add_argument('--threshold', dest='keyword_threshold', type=int, help='How many times does a phrase have to occur in the titles to be considered a keyword', default=2)
        argparser.add_argument('--keywords', dest='aging_keywords', help='Path to the text file containing extracted aging keywords', default='filtered_aging_keywords.txt')

    def prepare(self, args):
        with open(args.aging_keywords, 'r') as aging_keywords:
            self.keywords_list = aging_keywords.read().split('\n')
        self.keyword_threshold = args.keyword_threshold

    def keywords(self, tokens):
        keyword_counts = [(k, tokens.count(k)) for k in self.keywords_list if tokens.count(k) >= self.keyword_threshold]
        keyword_counts = sorted(keyword_counts, key=lambda kw_count: -kw_count[1])
        if len(keyword_counts) == 0:
            return []
        keywords, counts = zip(*keyword_counts)
        return keywords

def find_keywords(finder, processor, max_num_keywords=5):
    merged_titles = {id: ' '.join(titles) for id, titles in processor.extract_title_tokens().items()}
    merged_meshes = {id: ' '.join(meshes) for id, meshes in processor.extract_mesh_tokens().items()}
    keywords = {id: (finder.keywords(merged_titles[id] + ' ' + merged_meshes[id])[:max_num_keywords])
                    for id in papers.keys()}
    # remove potential duplicates.
    keywords = {id: list(set(kw)) for id, kw in keywords.items()}
    names = processor.extract_researcher_names()
    keywords = {
        id: {'researcher': names[id], 'keywords': keywords[id]}
        for id in keywords.keys()
    }
    return keywords

def filter_generics(finder, keywords, unique_threshold = 10):
    num_researchers = len([id for id, v in keywords.items() if len(v['keywords']) > 0])
    unique_th = unique_threshold * num_researchers // 100
    merged_keywords = list( itertools.chain.from_iterable(v['keywords'] for v in keywords.values()))
    generics = [kw for kw in finder.keywords_list if merged_keywords.count(kw) > unique_th]
    print('Found generics:')
    print(generics)
    return [kw for kw in keywords if kw not in set(generics)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find keywords in a set of papers')
    parser.add_argument('--in', dest='input', help='Path to the json file containing crawled papers', default='papers.json')
    parser.add_argument('--out', dest='output', help='Path to the csv file where to store found keywords', default='keywords.csv')
    parser.add_argument(    '--max_keywords', dest='max_keywords', type=int, help='Maximum number of keywords to assign a researcher', default=5)

    tokenizer = Tokenizer()
    tokenizer.register_options(parser)
    finder = KeywordsFinder()
    finder.register_options(parser)

    args = parser.parse_args()
    finder.prepare(args)
    tokenizer.prepare(args)

    def format(k):
        if ', ' in k:
            p1, p2 = k.split(', ')
            return p2 + ' ' + p1
        return k

    with open(args.input, 'r') as input, \
         open(args.output, 'w') as output:
        papers = json.load(input)
        processor = PubmedProcessor(papers, tokenizer.tokenize)
        keywords = find_keywords(finder, processor, max_num_keywords=args.max_keywords)
        keywords_csv = [
            ';'.join([id, k['researcher'], ', '.join([format(kw) for kw in k['keywords']])])
            for id, k in keywords.items()
        ]
        output.write('\n'.join(keywords_csv))
