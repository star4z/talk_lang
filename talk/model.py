import ast

A = 'a'
AN = 'an'
THE = 'the'
articles = (A, AN, THE)

AM = 'am'
IS = 'is'
ARE = 'are'
WAS = 'was'
WERE = 'were'
BE = 'be'
BEING = 'being'
BEEN = 'been'
HAS = 'has'
HAVE = 'have'
HAD = 'had'
DOES = 'does'

verbs = (AM, IS, ARE, WAS, WERE, BE, BEING, BEEN, HAS, HAVE, HAD, DOES)

WHAT = 'what'
OF = 'of'

VERB = 'verb'
SUBJECT = 'subj'
OBJECT = 'obj'
ARTICLE = 'article'

DECLARATIVE = 'declarative'
INTERROGATIVE = 'interrogative'

END_LINES = {'.': DECLARATIVE, '?': INTERROGATIVE}

EXPRESSION_TOKENS = {'+', '-', '*', '/', '(', ')'}


def normalize_key(noun):
    if isinstance(noun, Noun):
        noun = noun.value()
    if isinstance(noun, str):
        return noun.lower()
    return noun


def is_quoted_literal(token):
    return (len(token) >= 2 and ((token[0] == token[-1] == '"') or (token[0] == token[-1] == "'")))


def parse_literal(token):
    if is_quoted_literal(token):
        return Noun(token[1:-1])
    try:
        if '.' in token:
            float(token)
            return Noun(token)
        int(token)
        return Noun(token)
    except ValueError:
        return Noun(token)


def looks_like_expression(tokens):
    return any(token in EXPRESSION_TOKENS for token in tokens)


def evaluate_expression(tokens):
    expr = ' '.join(tokens)
    node = ast.parse(expr, mode='eval')
    for sub in ast.walk(node):
        if not isinstance(sub, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd, ast.Load, ast.Tuple, ast.Call, ast.Name)):
            raise ValueError("Unsupported expression")
        if isinstance(sub, ast.Name):
            raise ValueError("Unsupported name in expression")
        if isinstance(sub, ast.Call):
            raise ValueError("Function calls not supported")
    result = eval(compile(node, '<string>', 'eval'))
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return Noun(str(result))


def remove_apostrophe(word):
    return word[:word.index("'")]


class Verb:
    def __init__(self, value, req_params):
        self.value = value
        self.req_params = req_params

    def do(self, *args):
        if len(args) != len(self.req_params) \
                or any(arg for i, arg in enumerate(args) if self.req_params[i] != type(args)):
            raise ValueError("")


class Noun:
    def __init__(self, value, supertypes=()):
        self._value = value
        self._fields = dict()
        self._supertypes = supertypes + ('Noun',)
        self._actions = []

    def value(self):
        return self._value

    def __str__(self):
        return str(self.value())

    def __repr__(self):
        return repr(self.value())

    def __getitem__(self, item):
        return self._fields[self.uncast(item)]

    def __setitem__(self, key, value):
        v = self.cast(value)
        v._supertypes = v._supertypes + (key,)
        self._fields[self.uncast(key)] = v

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if self.uncast(name) in self._fields:
            return self._fields[self.uncast(name)]
        raise AttributeError(name)

    def __contains__(self, item):
        return self.uncast(item) in self._fields

    def __iter__(self):
        return iter(self._fields)

    def __eq__(self, other):
        o = self.cast(other)
        return self.value() == o.value()

    def has_a(self, noun):
        return any(field for field, value in self._fields.items() if value.is_a(self.uncast(noun)))

    @staticmethod
    def uncast(noun):
        if isinstance(noun, Noun):
            noun = noun.value()
        if isinstance(noun, str):
            return noun.lower()
        return noun

    def is_a(self, noun):
        return noun in self._supertypes

    def supertypes(self):
        return self._supertypes

    @staticmethod
    def cast(noun):
        return noun if isinstance(noun, Noun) else Noun(noun)


class ActionRule:
    def __init__(self, condition, target, expression):
        self.condition = condition
        self.target = target
        self.expression = expression


class ActionDefinition:
    def __init__(self, class_name, action_name):
        self.class_name = class_name
        self.action_name = action_name
        self.parameters = []
        self.rules = []
