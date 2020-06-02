import unittest

from find_keywords import KeywordsFinder


class FindKeywordsTest(unittest.TestCase):

    def test_find_keywords(self):
        finder = KeywordsFinder()
        finder.keywords_list = ['kw']
        finder.keyword_threshold = 2

        self.assertEqual(finder.keywords({1: ['kw', 'a'], 2: ['kw', 'a']}), ('kw',))

    def test_find_keywords_no_double_counting(self):
        finder = KeywordsFinder()
        finder.keywords_list = ['kw']
        finder.keyword_threshold = 2

        self.assertEqual(finder.keywords({1: ['kw', 'kw']}), ())

    def test_find_keywords_exact_match(self):
        finder = KeywordsFinder()
        finder.keywords_list = ['kw']
        finder.keyword_threshold = 1

        self.assertEqual(finder.keywords({1: ['kw kw']}), ())

    def test_find_keywords_sorted(self):
        finder = KeywordsFinder()
        finder.keywords_list = ['kw1', 'kw2']
        finder.keyword_threshold = 1

        self.assertEqual(finder.keywords({1: ['kw1', 'kw2'], 2: ['kw2']}), ('kw2', 'kw1'))

if __name__ == '__main__':
    unittest.main()
