import argparse
import json

from nltk.probability import FreqDist

from tokenize import Tokenizer

class KeywordsExtractor(object):

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def is_redundant(self, cand, keywords):
        for k in keywords:
            if cand in k and not cand is k:
                return True
        return False

    def keywords(self, text, num=10):
        # TODO: looks good, but should I also split hyphens?
        tokens = self.tokenizer(text)
        if len(tokens) == 0:
            return []
        token_pairs =  ['{} {}'.format(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]
        token_triplets = ['{} {} {}'.format(*tokens[i:i+3]) for i in range(len(tokens)-2)]
        tokens += token_pairs + token_triplets
        freqs = FreqDist(tokens)
        freqs = [(key, freq*len(key.split(' '))) for key, freq in freqs.items()]
        freqs = sorted(freqs, key=lambda word_freq: -word_freq[1])
        keywords, freqs = zip(*freqs)
        if num:
            keywords = keywords[:num]
        keywords = [keyword for keyword in keywords if not self.is_redundant(keyword, keywords)]
        return keywords

def extract_keywords(papers, extractor: KeywordsExtractor, num):
    merged_titles = {id: ' '.join(researcher['papers']) for id, researcher in papers.items()}
    all_titles = ' '.join(merged_titles.values())
    return extractor.keywords(all_titles, num=num)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute potential keywords from a set of papers')
    parser.add_argument('--in', dest='input', help='Path to file containing crawled paper titles', default='papers.json')
    parser.add_argument('--out', dest='output', help='Path to the file where to store keywords', default='aging_keywords.txt')
    parser.add_argument('--num', dest='num', type=int, help='Number of keyword candidates to produce', default=400)
    tokenizer = Tokenizer()
    tokenizer.register_options(parser)
    args = parser.parse_args()
    tokenizer.prepare(args)
    extractor = KeywordsExtractor(tokenizer.tokenize)
    with open(args.input, 'r') as input, open(args.output, 'w') as output:
        papers = json.load(input)
        aging_keywords = extract_keywords(papers, extractor, args.num)
        output.write('\n'.join(aging_keywords))
