import json
import argparse
import nltk
from nltk.probability import FreqDist

from tokenize import Tokenizer


class KeywordsFinder(object):

    def __init__(self, tokenizer=Tokenizer()):
        self.tokenizer = tokenizer

    def register_options(self, argparser):
        self.tokenizer.register_options(argparser)
        argparser.add_argument('--threshold', dest='keyword_threshold', type=int, help='How many times does a phrase have to occur in the titles to be considered a keyword', default=2)
        argparser.add_argument('--keywords', dest='aging_keywords', help='Path to the text file containing extracted aging keywords', default='filtered_aging_keywords.txt')

    def prepare(self, args):
        self.tokenizer.prepare(args)
        with open(args.aging_keywords, 'r') as aging_keywords:
            self.keywords_list = aging_keywords.read().split('\n')
        self.keyword_threshold = args.keyword_threshold

    def keywords(self, text):
        tokens = self.tokenizer.tokenize(text)
        merged_tokens = ' '.join(tokens)
        return [k for k in self.keywords_list if merged_tokens.count(k) >= self.keyword_threshold]

def find_keywords(papers, finder, max_num_keywords=5):
    merged_titles = {id: ' '.join(researcher['papers']) for id, researcher in papers.items()}
    keywords = {id: finder.keywords(merged_title)[:max_num_keywords] for id, merged_title in merged_titles.items()}
    keywords = {
        id: {'researcher': papers[id]['researcher'], 'keywords': k}
        for id, k in keywords.items()
    }
    return keywords

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find keywords in a set of papers')
    parser.add_argument('--in', dest='input', help='Path to the json file containing crawled papers', default='papers.json')
    parser.add_argument('--out', dest='output', help='Path to the csv file where to store found keywords', default='keywords.csv')
    parser.add_argument('--max_keywords', dest='max_keywords', type=int, help='Maximum number of keywords to assign a researcher', default=5)

    finder = KeywordsFinder()
    finder.register_options(parser)
    args = parser.parse_args()
    finder.prepare(args)

    with open(args.input, 'r') as input, \
         open(args.output, 'w') as output:
        papers = json.load(input)
        keywords = find_keywords(papers, finder, max_num_keywords=args.max_keywords)
        keywords_csv = [
            ';'.join([id, k['researcher'], ', '.join(k['keywords'])])
            for id, k in keywords.items()
        ]
        output.write('\n'.join(keywords_csv))
