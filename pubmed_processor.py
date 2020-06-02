import argparse
import json
import traceback

from tokenizer import Tokenizer

class PubmedProcessor:

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def extract_info(self, papers):
        return {
            res_id: {'researcher': res['researcher'], 'papers': self._extract_info_per_researcher(res['papers'])}
            for res_id, res in papers.items()
        }

    def _compute_tokens_from_title(self, title):
        tokens = self.tokenizer(title)
        token_pairs =  ['{} {}'.format(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]
        token_triplets = ['{} {} {}'.format(*tokens[i:i+3]) for i in range(len(tokens)-2)]
        tokens += token_pairs + token_triplets
        return tokens

    def _extract_info_per_researcher(self, papers: dict) -> dict:
        return {paper_id: self._extract_info_per_paper(paper) for paper_id, paper in papers.items()}

    def _extract_info_per_paper(self, paper):
        info = {
         'title': [],
         'meshes': [],
         'other': []
        }
        medline = paper['PubmedArticleSet']['PubmedArticle']['MedlineCitation']
        info['title'] = self._compute_tokens_from_title(self._maybe_str(medline['Article']['ArticleTitle']).lower())
        if 'MeshHeadingList' in medline.keys():
            try:
                info['meshes'] = [mesh['DescriptorName']['#text'].lower()
                    for mesh in self._maybe_list(medline['MeshHeadingList']['MeshHeading'])]
            except Exception as ex:
                print(paper)
                traceback.print_exc()
        if 'KeywordList' in medline.keys():
            try:
                info['other'] =  [self._maybe_str(kw).lower() for kw in self._maybe_list(medline['KeywordList']['Keyword'])]
            except Exception as ex:
                print(paper)
                traceback.print_exc()
        return info

    def _maybe_list(self, xml):
        return xml if isinstance(xml, list) else [xml]

    def _maybe_str(self, xml):
        return xml['#text'] if '#text' in xml else xml


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract info from crawled pubmed database.')
    parser.add_argument('--in', dest='input', help='Path to the json file containing crawled papers', default='papers.json')
    parser.add_argument('--out', dest='output', help='Path to the csv file where to store found keywords', default='processed_papers.json')

    tokenizer = Tokenizer()
    tokenizer.register_options(parser)

    args = parser.parse_args()
    tokenizer.prepare(args)

    processor = PubmedProcessor(tokenizer.tokenize)

    with open(args.input, 'r') as input, \
         open(args.output, 'w') as output:
        papers = json.load(input)
        processed_papers = processor.extract_info(papers)
        json.dump(processed_papers, output)
