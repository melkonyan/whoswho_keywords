import argparse
import json
import traceback
import itertools

from nltk.probability import FreqDist

from tokenizer import Tokenizer
from pubmed_processor import PubmedProcessor

class KeywordsExtractor(object):

    def is_redundant(self, cand, keywords):
        # TODO: this can be a performance bottleneck
        for k in keywords:
            if cand in k and not cand is k:
                return True
        return False

    def extract_keywords(self, tokens, num=10, remove_redundant=True):
        freqs = FreqDist(tokens)
        freqs = [(key, freq*len(key.split(' '))) for key, freq in freqs.items()]
        freqs = sorted(freqs, key=lambda word_freq: -word_freq[1])
        keywords, freqs = zip(*freqs)
        if num:
            keywords = keywords[:num]
        if remove_redundant:
            keywords = [keyword for keyword in keywords if not self.is_redundant(keyword, keywords)]
        return keywords


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute potential keywords from a set of papers')
    parser.add_argument('--in', dest='input', help='Path to file containing crawled paper titles', default='papers.json')
    parser.add_argument('--out', dest='output', help='Path to the file where to store keywords', default='aging_keywords.txt')
    parser.add_argument('--num', dest='num', type=int, help='Number of keyword candidates to produce', default=400)
    tokenizer = Tokenizer()
    tokenizer.register_options(parser)
    args = parser.parse_args()
    tokenizer.prepare(args)
    extractor = KeywordsExtractor()
    with open(args.input, 'r') as input, open(args.output, 'w') as output:
        papers = json.load(input)
        processor = PubmedProcessor(papers, tokenizer.tokenize)
        title_keywords = extractor.extract_keywords(itertools.chain.from_iterable(processor.extract_title_tokens().values()), args.num, remove_redundant=True)
        mesh_keywords = extractor.extract_keywords(itertools.chain.from_iterable(processor.extract_mesh_tokens().values()), args.num, remove_redundant=False)
        output.write('### Keywords extracted from titles\n')
        output.write('\n'.join(title_keywords))
        output.write('\n### Mesh-keywords\n')
        output.write('\n'.join(mesh_keywords))
