# END_LINES = '[.?\n]'


A = 'a'  # nonspecific article
AN = 'an'
THE = 'the'  # specific article
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

WHAT = 'what'  # query operator

OF = 'of'

import ast
import re

# Word classifications
VERB = 'verb'
SUBJECT = 'subj'
OBJECT = 'obj'
ARTICLE = 'article'

# Sentence classifications
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


def filter_articles(words):
    return [word for word in words if word.lower() not in articles]


def remove_apostrophe(word):
    return word[:word.index("'")]


class Verb:
    def __init__(self, value, req_params):
        self.value = value
        # req_params is a tuple of types, where the length indicates the number of parameters
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

    def supertypes(self):
        return self._supertypes

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

    @staticmethod
    def cast(noun):
        """Converts all non-Nouns to Nouns"""
        return noun if isinstance(noun, Noun) else Noun(noun)


class Talk(Noun):
    """
    Main class for Talk lang.
    Can be used by calling Talk("Some sentence") for convenience, and also with .talk("Some sentence") for repeated
    calls on a Talk object.
    """

    def __init__(self, line='', print_mode=False):
        super().__init__('root Talk Noun')
        self.classes = {}
        self.output = ''
        self.print_mode = print_mode

        self.talk(line)

    def talk(self, line):
        # Sentences are determined by punctuation, not lines, so ignore line breaks.
        line = ''.join(line.split('\n'))
        # Stores the index of the beginning character of the current sentence.
        last_end = 0

        # Look through letters to find characters denoting end of sentences, and then handle that sentence.
        for i, c in enumerate(line):
            # TODO: handle case where the period denotes a float, or other similar cases like website names.
            if c in END_LINES:
                self.sentence(line[last_end:i], END_LINES[c])
                last_end = i + 1
        if last_end < len(line):
            remaining = line[last_end:].strip()
            if remaining:
                self.sentence(remaining, DECLARATIVE)

    def __str__(self):
        if self.output:
            return self.output
        if len(self._fields) == 1:
            value = next(iter(self._fields.values()))
            return str(value) + '\n'
        return self.output

    def strip_leading_articles(self, words):
        if not words:
            return words
        if len(words) == 1 and words[0].lower() in articles:
            return words
        if words[0].lower() == 'a' and self.uncast(words[0]) in self._fields:
            return words
        return words[1:] if words[0].lower() in articles else words

    def print(self, line):
        if self.print_mode:
            print(line)
        self.output += str(line) + '\n'

    def sentence(self, sentence, sentence_type):
        words = [word for word in sentence.split(' ') if word]
        verb_index = next((i for i, word in enumerate(words) if word.lower() in verbs), None)
        if verb_index is not None:
            verb = words[verb_index].lower()
            if sentence_type == DECLARATIVE:
                subj = self.strip_leading_articles(words[:verb_index])
                if verb == DOES:
                    next_word = words[verb_index + 1].lower() if verb_index + 1 < len(words) else ''
                    next_next = words[verb_index + 2].lower() if verb_index + 2 < len(words) else ''
                    if next_word == HAVE:
                        self.create_object_if_needed(subj[0])
                        obj = self.strip_leading_articles(words[verb_index + 2:])
                        self.handle_verb(obj, subj, HAS)
                    elif next_word == 'not' and next_next == HAVE:
                        self.create_object_if_needed(subj[0])
                    else:
                        obj = self.strip_leading_articles(words[verb_index + 1:])
                        self.handle_verb(obj, subj, verb)
                else:
                    obj = self.strip_leading_articles(words[verb_index + 1:])
                    self.handle_verb(obj, subj, verb)
            elif sentence_type == INTERROGATIVE:
                query = words[0].lower()
                if query == WHAT and verb == IS:
                    obj = self.strip_leading_articles(words[verb_index + 1:])
                    result = self.resolve_query(obj)
                    self.print(result)
                elif query == DOES:
                    subj = words[verb_index - 1] if verb == HAVE else (words[verb_index + 1] if verb == DOES and verb_index + 2 < len(words) and words[verb_index + 2].lower() == HAVE else None)
                    if subj is None:
                        return
                    obj_index = (verb_index + 1) if verb == HAVE else (verb_index + 3)
                    obj = filter_articles(words[obj_index:])
                    if self.uncast(subj) not in self._fields:
                        self.print("I don't know.")
                    else:
                        result = self[subj].has_a(obj[0])
                        self.print("yes" if result else "no")

    def resolve_query(self, obj):
        if not obj:
            return ""
        if looks_like_expression(obj):
            resolved = [self._resolve_expression_token(token) for token in obj]
            return evaluate_expression(resolved)
        if len(obj) == 1:
            token = obj[0]
            if is_quoted_literal(token):
                return parse_literal(token)
            if token.isdigit() or self.is_number_like(token):
                return parse_literal(token)
            if self.uncast(token) in self._fields:
                return self[token]
            return parse_literal(token)
        if len(obj) == 2 and "'" in obj[0]:
            # Possessive query like "Ben's height": treat the first token as
            # a subject and the second token as a field on that subject.
            head = remove_apostrophe(obj[0])
            return self[head][obj[1]]
        if len(obj) == 2:
            # Two-token queries can mean either:
            #   1) "<subject> <field>" when the first token is a known object,
            #      e.g. "Ben height".
            #   2) If the first token is not known but the second token is,
            #      return the second token as the referenced object.
            #   3) Otherwise, interpret the phrase as a literal value.
            if self.uncast(obj[0]) in self._fields:
                return self[obj[0]][obj[1]]
            return self[obj[1]] if self.uncast(obj[1]) in self._fields else parse_literal(' '.join(obj))
        if len(obj) >= 3 and obj[1].lower() == OF:
            # Queries of the form "<field> of <object>", e.g. "height of Ben" or
            # "name of my friend". Supports multi-word object targets.
            field = obj[0]
            target = ' '.join(obj[2:])
            if is_quoted_literal(target) or target.isdigit() or self.is_number_like(target):
                if field.lower() == 'value':
                    # Special case for "value of <literal>", which just returns the literal value,
                    # since it doesn't make sense to have a field called "value" on a literal.
                    return parse_literal(target)
                # If the target is a literal but the field is not "value", then interpret the whole
                # thing as a literal, since it doesn't make sense to query a field on a literal.
                return parse_literal(target)
            if field.lower() == 'value':
                # Special case for "value of <object>", which just returns the object itself, since
                # the "value" field is implicit on all objects.
                try:
                    return self[target]
                except KeyError:
                    return "I don't know."
            # For non-literal targets, if the target is known, return the field on that target.
            try:
                return self[target][field]
            except KeyError:
                return "I don't know."
        # For longer queries that don't match any of the above patterns, interpret as a literal value.
        return parse_literal(' '.join(obj))

    @staticmethod
    def is_number_like(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _resolve_expression_token(self, token):
        if token in EXPRESSION_TOKENS:
            return token
        if is_quoted_literal(token):
            value = parse_literal(token).value()
            return str(value)
        if token.isdigit() or self.is_number_like(token):
            return token
        if self.uncast(token) in self._fields:
            value = self[token].value()
            return str(value)
        return token

    def handle_verb(self, obj, subj, verb):
        if verb == IS:
            self.handle_is(obj, subj)
        elif verb == HAS:
            self.handle_has(obj, subj)

    def handle_has(self, obj, subj):
        if len(subj) > 0:
            subject = subj[0]
            self.create_object_if_needed(subject)
            if len(subj) > 1 and 'not' in [word.lower() for word in subj]:
                return
            if len(obj) == 1:
                self[subject][obj[0]] = self.create_object_if_needed(obj[0])
            elif OF in obj and len(obj) == 3:
                self[subject][obj[0]] = obj[2]

    def handle_is(self, obj, subj):
        subj = self.strip_leading_articles(subj)

        # variable assignment, ie, "a" is "b"
        if len(subj) == 1 and len(obj) == 1:
            if is_quoted_literal(obj[0]) or self.is_number_like(obj[0]):
                self[subj[0]] = parse_literal(obj[0])
            else:
                self.classes[obj[0]] = type(obj[0], (), {})
                self[subj[0]] = Noun(obj[0], supertypes=(obj[0],))
        # attribute assignment, ie, "a's b" is "c"
        elif len(subj) == 2 and "'" in subj[0] and len(obj) == 1:
            subject = remove_apostrophe(subj[0])
            self.create_object_if_needed(subject)
            self.create_object_if_needed(subj[1])
            self[subject][subj[1]] = parse_literal(obj[0])
        # assignment of a field on an object, ie, "My name is Ben"
        elif len(subj) == 2 and len(obj) == 1:
            subject = subj[0]
            field = subj[1]
            self.create_object_if_needed(subject)
            self[subject][field] = parse_literal(obj[0])
        # case "a of b" is "c" (attribute assignment or variable assignment for value)
        elif len(subj) == 3 and OF in subj and len(obj) == 1:
            adj = subj[0]
            head = subj[2]
            if adj.lower() == 'value':
                self[head] = parse_literal(obj[0])
            else:
                self.create_object_if_needed(head)
                self[head][adj] = parse_literal(obj[0])

    def create_object_if_needed(self, obj):
        # if not hasattr(self, obj):
        #     # Create generic "object" type and add it to the stored types
        #     object_type = type('object', (), {})
        #     self.classes['object'] = object_type
        #     # Adds subject as an 'object' to this root object
        #     instance = object_type()
        #     setattr(self, obj, instance)
        #     return instance
        # else:
        #     return getattr(self, obj)
        if obj not in self:
            self[obj] = obj
        return self[obj]


def main():
    print("TALK")
    t = Talk(print_mode=True)
    line = ''
    while line != 'quit':
        line = input()
        t.talk(line)
    print("THANKS BYE")


if __name__ == '__main__':
    main()
