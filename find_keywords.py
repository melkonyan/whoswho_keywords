from rake_nltk import Rake, Metric
import operator
import json
import argparse
import nltk
from nltk.probability import FreqDist
import itertools
import re
import string

from tokenize import Tokenizer

stop_dir = "rake_stoplist.txt"

def compute_general_words(threshold=10):
     nltk.download('gutenberg')
     emma = nltk.corpus.gutenberg.words('austen-emma.txt')
     freqs = sorted([(keyword, freq) for keyword, freq in FreqDist(emma).items()], key=lambda freq: -freq[1])
     return [keyword for keyword, freq in freqs if freq > threshold]


class RakeKeywords(object):
    def __init__(self):
        stopwords = compute_general_words()
        self.rake = Rake(
            stopwords=stopwords,
            max_length=2,
            ranking_metric=Metric.WORD_FREQUENCY)

    def keywords(self, text):
        self.rake.extract_keywords_from_text(text)
        keywords = self.rake.get_ranked_phrases()
        #keywords, score = zip(*keywords)
        return keywords


class KeywordsFinder(object):

    def __init__(self, keywords, tokenizer):
        self.tokenizer = tokenizer
        self.keywords_list = keywords

    def keywords(self, text, threshold=2):
        tokens = self.tokenizer(text)
        merged_tokens = ' '.join(tokens)
        return [k for k in self.keywords_list if merged_tokens.count(k) >= threshold]

def find_keywords(papers, finder, max_num_keywords=5):
    merged_titles = {id: ' '.join(researcher['papers']) for id, researcher in papers.items()}
    keywords = {id: finder.keywords(merged_title)[:max_num_keywords] for id, merged_title in merged_titles.items()}
    keywords = {
        id: {'researcher': papers[id]['researcher'], 'keywords': k}
        for id, k in keywords.items()
    }
    return keywords

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--in', dest='input', help='Path to the json file containing crawled papers', default='papers.json')
    parser.add_argument('--out', dest='output', help='Path to the csv file where to store found keywords', default='keywords.csv')
    parser.add_argument('--keywords', dest='aging_keywords', help='Path to the text file containing extract aging keywords', default='filtered_aging_keywords.txt')
    tokenizer = Tokenizer()
    tokenizer.register_options(parser)
    args = parser.parse_args()
    tokenizer.prepare(args)
    with open(args.input, 'r') as input, \
         open(args.aging_keywords, 'r') as aging_keywords, \
         open(args.output, 'w') as output:
        papers = json.load(input)
        aging_keywords = aging_keywords.read().split('\n')
        finder = KeywordsFinder(aging_keywords, tokenizer.tokenize)
        keywords = find_keywords(papers, finder)
        keywords_csv = [
            ';'.join([id, k['researcher'], ', '.join(k['keywords'])])
            for id, k in keywords.items()
        ]
        output.write('\n'.join(keywords_csv))
