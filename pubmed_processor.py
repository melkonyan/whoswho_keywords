import traceback

class PubmedProcessor:

    def __init__(self, papers: dict, tokenizer):
        self.tokenizer = tokenizer
        self.papers = papers
        self.extracted_info = None

    def extract_title_tokens(self) -> dict:
        self._extract_info()

        def compute_tokens(titles):
            tokens = self.tokenizer(' '.join(titles))
            token_pairs =  ['{} {}'.format(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]
            token_triplets = ['{} {} {}'.format(*tokens[i:i+3]) for i in range(len(tokens)-2)]
            tokens += token_pairs + token_triplets
            return tokens

        return {id: compute_tokens(titles) for id, titles in self.extracted_info['titles'].items()}

    def extract_mesh_tokens(self) -> dict:
        self._extract_info()
        return self.extracted_info['meshes']

    def extract_researcher_names(self):
        return {id: v['researcher'] for id, v in self.papers.items()}

    def _extract_info(self):
        if self.extracted_info is not None:
            return
        info_per_reseacher = {id: self._extract_info_per_researcher(res['papers'].values()) for id, res in self.papers.items()}
        self.extracted_info = {
            'titles': {id: titles for id, (_, titles, _) in info_per_reseacher.items()},
            'meshes': {id: meshes for id, (meshes, _, _) in info_per_reseacher.items()},
            'other_keywords': {id: other for id, (_, _, other) in info_per_reseacher.items()},
        }

    def _extract_info_per_researcher(self, papers):
        mesh_terms = []
        titles = []
        other_keywords = []
        for paper_details in papers:
            medline = paper_details['PubmedArticleSet']['PubmedArticle']['MedlineCitation']
            titles.append(self._maybe_str(medline['Article']['ArticleTitle']))
            if 'MeshHeadingList' in medline.keys():
                try:
                    mesh_terms += [mesh['DescriptorName']['#text'].lower()
                        for mesh in self._maybe_list(medline['MeshHeadingList']['MeshHeading'])]
                except Exception as ex:
                    print(paper_details)
                    traceback.print_exc()
            if 'KeywordList' in medline.keys():
                try:
                    other_keywords += [kw['#text'].lower() for kw in self._maybe_list(medline['KeywordList']['Keyword'])]
                except Exception as ex:
                    print(paper_details)
                    traceback.print_exc()
        return mesh_terms, titles, other_keywords

    def _maybe_list(self, xml):
        return xml if isinstance(xml, list) else [xml]

    def _maybe_str(self, xml):
        return xml['#text'] if '#text' in xml else xml
