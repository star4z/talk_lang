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
        """Converts all non-Nouns to Nouns"""
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


class Talk(Noun):
    """
    Main class for Talk lang.
    Can be used by calling Talk("Some sentence") for convenience, and also with .talk("Some sentence") for repeated
    calls on a Talk object.
    """

    def __init__(self, line='', print_mode=False):
        super().__init__('root Talk Noun')
        self.classes = {}
        self.actions = {}
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
        sentence = sentence.strip()
        if not sentence:
            return
        words = [word for word in sentence.split(' ') if word]
        category = self.categorize_sentence(sentence, sentence_type)

        # Support additional sentence shapes beyond simple declarative/interrogative
        # such as action definition and conditional rule declarations.
        if category == 'when':
            self.handle_when(sentence)
            return

        if category == 'action_definition':
            self.handle_action_definition(sentence)
            return

        # Try executing explicit action invocation forms before falling back to
        # normal subject-verb-object handling.
        if self.try_handle_action_invocation(words):
            return

        verb_index = next((i for i, word in enumerate(words) if word.lower() in verbs), None)
        if verb_index is not None:
            verb = words[verb_index].lower()
            if category == DECLARATIVE:
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
            elif category == INTERROGATIVE:
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
                        self.print(self.unknown_result())
                    else:
                        result = self[subj].has_a(obj[0])
                        self.print("yes" if result else "no")
                elif query in (IS, ARE):
                    subj = self.strip_leading_articles(words[verb_index + 1:verb_index + 2])
                    obj = self.strip_leading_articles(words[verb_index + 2:])
                    if not subj or self.uncast(subj[0]) not in self._fields:
                        self.print(self.unknown_result())
                    else:
                        subject = self[subj[0]]
                        if obj and (subject.is_a(obj[0]) or subject.has_a(obj[0])):
                            self.print("yes")
                        else:
                            self.print("no")

    def categorize_sentence(self, sentence, sentence_type):
        """Classify the sentence by content and punctuation.

        The system uses the punctuation-derived sentence type as a base, but
        supports additional declarative sentence forms for action definitions
        and conditional rules.
        """
        normalized = sentence.strip().lower()
        if normalized.startswith('when '):
            return 'when'
        if ' can ' in normalized or ' requires ' in normalized:
            return 'action_definition'
        if sentence_type == INTERROGATIVE:
            return INTERROGATIVE
        return DECLARATIVE

    def handle_action_definition(self, sentence):
        """Parse declarative action definitions like "A dummy can calculate." or
        "A dummy requires a number to calculate." and record the action metadata.
        """
        words = [word for word in sentence.rstrip('.').split(' ') if word]
        lower = [w.lower() for w in words]
        if 'can' in lower:
            idx = lower.index('can')
            class_name = self.strip_leading_articles(words[:idx])[0]
            action_name = self.normalize_action_name(words[idx + 1])
            self.define_action_for_class(class_name, action_name)
            return
        if 'requires' in lower and 'to' in lower:
            idx = lower.index('requires')
            to_idx = lower.index('to')
            class_name = self.strip_leading_articles(words[:idx])[0]
            param_tokens = self.strip_leading_articles(words[idx + 1:to_idx])
            param_name = self.uncast(param_tokens[-1]) if param_tokens else 'value'
            action_name = self.normalize_action_name(words[to_idx + 1])
            action_def = self.define_action_for_class(class_name, action_name)
            if param_name not in action_def.parameters:
                action_def.parameters.append(param_name)

    def handle_when(self, sentence):
        """Parse conditional action rules declared with a `When ... if ... then ...` sentence."""
        sentence = sentence.rstrip('.').strip()
        if sentence.lower().startswith('when '):
            sentence = sentence[5:]
        match = re.match(r'(.+?),\s*if\s+(.+?),\s*then\s+(.+)', sentence, re.I)
        if not match:
            return
        action_phrase, condition_text, effect_text = match.groups()
        subject_words = self.strip_leading_articles([word for word in action_phrase.split(' ') if word])
        if len(subject_words) < 2:
            return
        subject_name = self.uncast(subject_words[0])
        action_name = self.normalize_action_name(subject_words[1])
        action_def = self.define_action_for_class(subject_name, action_name)
        condition = self.parse_action_condition(condition_text)
        target, expression = self.parse_action_effect(effect_text)
        action_def.rules.append(ActionRule(condition, target, expression))

    def try_handle_action_invocation(self, words):
        """Detect and execute action invocation sentences like "The dummy calculates with 8."."""
        lower = [word.lower() for word in words]
        for i, word in enumerate(words):
            action_name = self.normalize_action_name(word)
            if i == 0:
                continue
            subject = self.strip_leading_articles(words[:i])
            if not subject:
                continue
            action_def = self.get_action_definition_for_subject(subject[0], action_name)
            if not action_def:
                continue
            params = {}
            if 'with' in lower[i + 1:]:
                with_index = lower.index('with', i + 1)
                param_expr = ' '.join(words[with_index + 1:])
                if param_expr:
                    param_value = self.evaluate_action_expression(param_expr, {}, subject[0], action_name)
                    param_name = action_def.parameters[0] if action_def.parameters else 'value'
                    params[param_name] = param_value
            self.execute_action(subject[0], action_name, params)
            return True
        return False

    def normalize_action_name(self, word):
        normalized = word.lower()
        if normalized.endswith('s'):
            candidate = normalized[:-1]
            if candidate in self.get_all_action_names() or candidate.endswith('e'):
                return candidate
        if normalized.endswith('ing'):
            root = normalized[:-3]
            if root in self.get_all_action_names():
                return root
            if root + 'e' in self.get_all_action_names():
                return root + 'e'
        return normalized

    def get_all_action_names(self):
        return {action_name for _, action_name in self.actions.keys()}

    def get_action_definition_for_subject(self, subject, action_name):
        subject_name = self.uncast(subject)
        if (subject_name, action_name) in self.actions:
            return self.actions[(subject_name, action_name)]
        if self.uncast(subject_name) in self._fields:
            target = self[subject_name]
            for supertype in target.supertypes():
                if (supertype, action_name) in self.actions:
                    return self.actions[(supertype, action_name)]
        return None

    def define_action_for_class(self, class_name, action_name):
        class_name = self.uncast(class_name)
        if class_name not in self.classes:
            self.classes[class_name] = type(class_name, (), {})
        key = (class_name, action_name)
        if key not in self.actions:
            self.actions[key] = ActionDefinition(class_name, action_name)
        return self.actions[key]

    def parse_action_condition(self, text):
        """Convert a condition phrase into a callable predicate for action rules."""
        tokens = [word for word in text.rstrip('.').split(' ') if word]
        tokens = filter_articles(tokens)
        lower = [word.lower() for word in tokens]
        if 'equals' in lower:
            idx = lower.index('equals')
            left = tokens[:idx]
            right = tokens[idx + 1:]
            return lambda params: self.evaluate_action_value(left, params) == self.evaluate_action_value(right, params)
        if 'is' in lower and 'greater' in lower and 'than' in lower:
            idx = lower.index('is')
            left = tokens[:idx]
            right = tokens[idx + 3:]
            return lambda params: self.evaluate_action_value(left, params) > self.evaluate_action_value(right, params)
        return lambda params: False

    def parse_action_effect(self, text):
        """Parse the effect portion of a rule and return a target plus expression."""
        tokens = [word for word in text.rstrip('.').split(' ') if word]
        target_tokens = filter_articles(tokens[:tokens.index('is')] if 'is' in [w.lower() for w in tokens] else tokens)
        lower = [word.lower() for word in tokens]
        if 'is' in lower:
            idx = lower.index('is')
            target = ' '.join(self.uncast(word) for word in target_tokens)
            expression = ' '.join(tokens[idx + 1:])
            return target, expression
        return None, text

    def evaluate_action_value(self, words, params):
        if len(words) == 1:
            token = words[0]
            key = token.lower()
            if key in params:
                return self.to_number(params[key])
            if token.isdigit() or self.is_number_like(token):
                return self.to_number(token)
            return self.to_number(parse_literal(token).value())
        return self.evaluate_action_expression(' '.join(words), params)

    def evaluate_action_expression(self, expression, params, subject=None, action_name=None):
        expression = expression.strip()
        # Auto-close nested calculating calls that use the README-style
        # "calculating (a, and calculating (b)" structure.
        expression = re.sub(r'(calculating\s*\([^\)]*?),(?=\s*and\s+calculating\s*\()', r'\1)', expression, flags=re.I)
        # Handle nested action calls first
        while True:
            match = re.search(r'calculating\s*\(', expression, re.I)
            if not match:
                break
            start = match.start()
            open_paren = expression.find('(', match.end() - 1)
            close_paren = self.find_matching_paren(expression, open_paren)
            if close_paren is None:
                break
            inner = expression[open_paren + 1:close_paren]
            value = self.evaluate_action_expression(inner, params, subject, action_name)
            if subject and action_name:
                action_def = self.get_action_definition_for_subject(subject, action_name)
                if action_def:
                    param_name = action_def.parameters[0] if action_def.parameters else 'value'
                    value = self.execute_action(subject, action_name, {param_name: value})
                    value = self.to_number(value)
            expression = expression[:start] + str(value) + expression[close_paren + 1:]
        lowered = expression.lower()
        if lowered.startswith('the sum of '):
            remainder = expression[len('the sum of '):]
            parts = self.split_top_level_terms(remainder)
            return sum(self.evaluate_action_expression(part, params, subject, action_name) for part in parts)
        if lowered.startswith('sum of '):
            remainder = expression[len('sum of '):]
            parts = self.split_top_level_terms(remainder)
            return sum(self.evaluate_action_expression(part, params, subject, action_name) for part in parts)
        return self.evaluate_math_expression(expression, params)

    def split_top_level_terms(self, text):
        terms = []
        current = []
        depth = 0
        for word in text.split(' '):
            lower = word.lower().strip(',')
            # Keep track of parentheses depth so we only split at top level.
            if '(' in word:
                depth += word.count('(')
            if ')' in word:
                depth -= word.count(')')
            if depth == 0 and lower in ('and', ','):
                if current:
                    terms.append(' '.join(current).strip())
                    current = []
            else:
                current.append(word.strip(','))
        if current:
            terms.append(' '.join(current).strip())
        return terms

    def find_matching_paren(self, text, open_index):
        depth = 0
        for i in range(open_index, len(text)):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
        return None

    def evaluate_math_expression(self, expression, params):
        tokens = []
        for token in expression.replace('(', ' ( ').replace(')', ' ) ').replace(',', ' ').split():
            lower = token.lower()
            # Map natural-language arithmetic words into operators before
            # evaluating the expression.
            if lower in articles or lower == 'and':
                continue
            if lower in ('plus', 'add', 'added'):
                tokens.append('+')
            elif lower in ('minus', 'subtract', 'subtracted'):
                tokens.append('-')
            elif lower in ('times', 'multiplied', 'multiply'):
                tokens.append('*')
            elif lower in ('divided', 'over', 'divide'):
                tokens.append('/')
            elif lower == 'number' and 'number' in params:
                tokens.append(str(self.to_number(params['number'])))
            elif lower in params:
                tokens.append(str(self.to_number(params[lower])))
            elif token.isdigit() or self.is_number_like(token):
                tokens.append(token)
            else:
                tokens.append(token)
        resolved = [self._resolve_expression_token(token) for token in tokens]
        result = evaluate_expression(resolved)
        return self.to_number(result.value())

    def to_number(self, value):
        if isinstance(value, Noun):
            value = value.value()
        if isinstance(value, str):
            return int(value) if value.isdigit() else float(value)
        return value

    def execute_action(self, subject, action_name, params):
        action_def = self.get_action_definition_for_subject(subject, action_name)
        if not action_def:
            return None
        self.create_object_if_needed(subject, supertypes=(self.uncast(subject),))
        normalized_params = {k.lower(): self.to_number(v) for k, v in params.items()}
        for rule in action_def.rules:
            if rule.condition(normalized_params):
                return self.apply_action_effect(subject, action_name, rule.target, rule.expression, normalized_params)
        return None

    def apply_action_effect(self, subject, action_name, target, expression, params):
        result = self.evaluate_action_expression(expression, params, subject, action_name)
        wrapped = Noun(str(result))
        if target == 'result':
            self['result'] = wrapped
        elif self.uncast(target) in self._fields:
            self[target] = wrapped
        else:
            self['result'] = wrapped
        return result

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
                subject = self[obj[0]]
                return subject[obj[1]] if obj[1] in subject else self.unknown_result()
            return self[obj[1]] if self.uncast(obj[1]) in self._fields else parse_literal(' '.join(obj))
        if len(obj) >= 3 and obj[1].lower() == OF:
            # Queries of the form "<field> of <object>", e.g. "height of Ben" or
            # "name of my friend". Supports multi-word object targets.
            field = obj[0]
            target = ' '.join(obj[2:])
            if is_quoted_literal(target) or target.isdigit() or self.is_number_like(target):
                if field.lower() == 'value':
                    # Don't treat a query like "value of 'foo'" or "value of 3" as an echo;
                    # such queries should return an unknown value.
                    return self.unknown_result()
                # If the target is a literal but the field is not "value", then interpret the whole
                # thing as a literal, since it doesn't make sense to query a field on a literal.
                return parse_literal(target)
            if field.lower() == 'value':
                # Special case for "value of <object>", which just returns the object itself, since
                # the "value" field is implicit on all objects.
                try:
                    return self[target]
                except KeyError:
                    return self.unknown_result()
            # For non-literal targets, if the target is known, return the field on that target.
            try:
                return self[target][field]
            except KeyError:
                return self.unknown_result()
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

    def create_object_if_needed(self, obj, supertypes=()):
        if obj not in self:
            self[obj] = Noun(obj, supertypes=supertypes)
        else:
            existing = self[obj]
            for st in supertypes:
                if st not in existing._supertypes:
                    existing._supertypes += (st,)
        return self[obj]

    def unknown_result(self):
        return "It is unknown."


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
