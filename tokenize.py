import re
import string

class Tokenizer(object):

    def register_options(self, argparser):
        argparser.add_argument('--ignore', dest='ignored_tokens',
                                help='Path to the file that contains common connector words which shouldn\'t be considered tokens are thus removed from the text',
                                default='ignored_tokens.txt')
        default_allowed_chars = string.ascii_letters + string.digits
        argparser.add_argument('--chars', dest='allowed_chars',
                               help='Characters that tokens consist of. Anything not in this list will be considered a delimiter.\n By default is set to "{}"'.format(default_allowed_chars),
                               default=default_allowed_chars
        )

    def prepare(self, args):
        with open(args.ignored_tokens, 'r') as f:
            self.ignored_tokens = set(f.read().split('\n'))
        self.allowed_chars = args.allowed_chars
        pattern = '[' + ''.join(['^'+c for c in self.allowed_chars])+ ']'
        self.replace_chars_regex = re.compile(pattern)
        self.remove_multi_spaces_regex = re.compile(' +')

    def tokenize(self, text):
        text = self.replace_chars_regex.sub(' ', text)
        text = self.remove_multi_spaces_regex.sub(' ', text)
        tokens = text.split(' ')
        tokens = [token.lower() for token in tokens]    
        tokens = [token
                  for token in tokens
                  if token not in self.ignored_tokens
                  ]
        return tokens
