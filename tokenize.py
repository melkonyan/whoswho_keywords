import re
import string

class Tokenizer(object):

    def __init__(self):
        allowed_chars = string.ascii_letters + string.digits
        pattern = '[' + ''.join(['^'+c for c in allowed_chars])+ ']'
        self.replace_chars_regex = re.compile(pattern)
        self.remove_multi_spaces_regex = re.compile(' +')
        self.special_chars = set(['.', ',', '!', '-', '?', ':', "'s"])

    def register_options(self, argparser):
        argparser.add_argument('--ignore', dest='ignored_tokens',
                                help='Path to the file that contains tokens that will be deleted from the text.',
                                default='ignored_tokens.txt')

    def prepare(self, args):
        with open(args.ignored_tokens, 'r') as f:
            self.common_words = set(f.read().split('\n'))

    def tokenize(self, text):
        text = self.replace_chars_regex.sub(' ', text)
        text = self.remove_multi_spaces_regex.sub(' ', text)
        tokens = text.split(' ')
        tokens = [token.lower()
                  for token in tokens
                  if token not in self.common_words and token not in self.special_chars
                  ]
        return tokens
