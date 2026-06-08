import re

from .model import (
    DECLARATIVE,
    END_LINES,
    INTERROGATIVE,
    IS,
    OF,
    WHAT,
    HAS,
    HAVE,
    DOES,
    Noun,
    ActionDefinition,
    ActionRule,
    parse_literal,
    is_quoted_literal,
    looks_like_expression,
    evaluate_expression,
    remove_apostrophe,
)
from .utils import filter_articles


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
        line = ''.join(line.split('\n'))
        last_end = 0

        for i, c in enumerate(line):
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
        if len(words) == 1 and words[0].lower() in ('a', 'an', 'the'):
            return words
        if words[0].lower() == 'a' and self.uncast(words[0]) in self._fields:
            return words
        return words[1:] if words[0].lower() in ('a', 'an', 'the') else words

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

        if category == 'when':
            self.handle_when(sentence)
            return

        if category == 'action_definition':
            self.handle_action_definition(sentence)
            return

        if self.try_handle_action_invocation(words):
            return

        verb_index = next((i for i, word in enumerate(words) if word.lower() in (IS, HAS, DOES, 'am', 'are', 'was', 'were', 'be', 'being', 'been')), None)
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
                elif query in (IS, 'are'):
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
        normalized = sentence.strip().lower()
        if normalized.startswith('when '):
            return 'when'
        if ' can ' in normalized or ' requires ' in normalized:
            return 'action_definition'
        if sentence_type == INTERROGATIVE:
            return INTERROGATIVE
        return DECLARATIVE

    def handle_action_definition(self, sentence):
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
        expression = re.sub(r'(calculating\s*\([^\)]*?),(?=\s*and\s+calculating\s*\()', r'\1)', expression, flags=re.I)
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
            if lower in ('a', 'an', 'the') or lower == 'and':
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
            head = remove_apostrophe(obj[0])
            return self[head][obj[1]]
        if len(obj) == 2:
            if self.uncast(obj[0]) in self._fields:
                subject = self[obj[0]]
                return subject[obj[1]] if obj[1] in subject else self.unknown_result()
            return self[obj[1]] if self.uncast(obj[1]) in self._fields else parse_literal(' '.join(obj))
        if len(obj) >= 3 and obj[1].lower() == OF:
            field = obj[0]
            target = ' '.join(obj[2:])
            if is_quoted_literal(target) or target.isdigit() or self.is_number_like(target):
                if field.lower() == 'value':
                    return self.unknown_result()
                return parse_literal(target)
            if field.lower() == 'value':
                try:
                    return self[target]
                except KeyError:
                    return self.unknown_result()
            try:
                return self[target][field]
            except KeyError:
                return self.unknown_result()
        return parse_literal(' '.join(obj))

    @staticmethod
    def is_number_like(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _resolve_expression_token(self, token):
        if token in ('+', '-', '*', '/', '(', ')'):
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
        if len(subj) == 1 and len(obj) == 1:
            if is_quoted_literal(obj[0]) or self.is_number_like(obj[0]):
                self[subj[0]] = parse_literal(obj[0])
            else:
                self.classes[obj[0]] = type(obj[0], (), {})
                self[subj[0]] = Noun(obj[0], supertypes=(obj[0],))
        elif len(subj) == 2 and "'" in subj[0] and len(obj) == 1:
            subject = remove_apostrophe(subj[0])
            self.create_object_if_needed(subject)
            self.create_object_if_needed(subj[1])
            self[subject][subj[1]] = parse_literal(obj[0])
        elif len(subj) == 2 and len(obj) == 1:
            subject = subj[0]
            field = subj[1]
            self.create_object_if_needed(subject)
            self[subject][field] = parse_literal(obj[0])
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
