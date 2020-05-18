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

verbs = (AM, IS, ARE, WAS, WERE, BE, BEING, BEEN, HAS, HAVE, HAD)

WHAT = 'what'  # query operator
DOES = 'does'

OF = 'of'

# Word classifications
VERB = 'verb'
SUBJECT = 'subj'
OBJECT = 'obj'
ARTICLE = 'article'

# Sentence classifications
DECLARATIVE = 'declarative'
INTERROGATIVE = 'interrogative'

END_LINES = {'.': DECLARATIVE, '?': INTERROGATIVE}


def filter_articles(words):
    return [word for word in words if word.lower() not in articles]


def remove_apostrophe(word):
    return word[:word.index("'")]


class Noun:
    def __init__(self, value, supertypes=()):
        self._value = value
        self._fields = dict()
        self._supertypes = supertypes + ('Noun',)

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

    def __iter__(self):
        return iter(self._fields)

    def __eq__(self, other):
        o = self.cast(other)
        return self.value() == o.value() and self.supertypes() == o.supertypes()

    def has_a(self, noun):
        return any(field for field, value in self._fields.items() if value.is_a(self.uncast(noun)))

    def is_a(self, noun):
        return noun in self._supertypes

    @staticmethod
    def cast(noun):
        """Converts all non-Nouns to Nouns"""
        return noun if isinstance(noun, Noun) else Noun(noun)

    @staticmethod
    def uncast(noun):
        return noun.value() if isinstance(noun, Noun) else noun


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

    def __str__(self):
        return self.output

    def print(self, line):
        if self.print_mode:
            print(line)
        self.output += str(line) + '\n'

    def sentence(self, sentence, sentence_type):
        words = [word for word in sentence.split(' ') if word]
        verb_index = next((i for i, word in enumerate(words) if word in verbs), None)
        if verb_index is not None:
            verb = words[verb_index]
            if sentence_type == DECLARATIVE:
                subj = words[:verb_index]
                obj = filter_articles(words[verb_index + 1:])
                self.handle_verb(obj, subj, verb)
            elif sentence_type == INTERROGATIVE:
                query = words[0].lower()
                # what is
                if query == WHAT and verb == IS:
                    obj = filter_articles(words[verb_index + 1:])
                    # case: "b of a"
                    if OF in obj and len(obj) == 3:
                        # result = getattr(getattr(self, obj[2]), obj[0])
                        result = self[obj[2]][obj[0]]
                        self.print(result)
                    # case "a's b"
                    elif len(obj) == 2 and "'" in obj[0]:
                        head = remove_apostrophe(obj[0])
                        # result = getattr(getattr(self, head), obj[1])
                        result = self[head][obj[1]]
                        self.print(result)
                    else:
                        # result = getattr(getattr(self, obj[2]), obj[0])
                        result = self[obj[2]][obj[0]]
                        self.print(result)
                # does a have b
                elif query == DOES and verb == HAVE:
                    subj = words[verb_index - 1]
                    obj = filter_articles(words[verb_index + 1:])
                    if not self.has_a(subj):
                        self.print("I don't know.")
                    else:
                        # result = hasattr(getattr(self, subj), obj[0])
                        result = self[subj].has_a(obj[0])
                        if result:
                            self.print("yes")
                        else:
                            self.print("no")

    def handle_verb(self, obj, subj, verb):
        if verb == IS:
            self.handle_is(obj, subj)
        elif verb == HAS:
            self.handle_has(obj, subj)

    def handle_has(self, obj, subj):
        # it's probably a field assignment (eg. subj "has a" field of value, where obj = ["field", "of", "value"]
        if OF in obj and len(obj) == 3 and len(subj) == 1:
            # create subject reference on this Talk object if it doesn't exist
            self.create_object_if_needed(subj[0])
            # Set self.subj.field = value (field = obj[0], value = obj[2])
            # setattr(getattr(self, subj[0]), obj[0], obj[2])
            self[subj[0]][obj[0]] = obj[2]

        # it's a field with no value; eg. obj has a subj
        elif len(obj) == 1 and len(subj) == 1:
            self.create_object_if_needed(subj[0])
            self[subj[0]][obj[0]] = self.create_object_if_needed(obj[0])

    def handle_is(self, obj, subj):
        subj = filter_articles(subj)

        # it's probably a variable assignment, ie, "a" is "b"
        if len(subj) == 1 and len(obj) == 1:
            class_name = obj[0]
            obj_type = type(class_name, (), {})
            self.classes[class_name] = obj_type
            # setattr(self, subj[0], obj_type())
            self[subj[0]] = Noun(obj[0], supertypes=(obj[0],))
        # it's probably an attribute assignment, ie, "a's b" is "c"
        elif len(subj) == 2 and "'" in subj[0] and len(obj) == 1:
            subject = remove_apostrophe(subj[0])
            self.create_object_if_needed(subject)
            self.create_object_if_needed(subj[1])
            # setattr(getattr(self, subject), subj[1], obj[0])
            self[subject][subj[1]] = obj[0]
        # case "a of b" is "c" (attribute assignment)
        elif len(subj) == 3 and OF in subj:
            adj = subj[0]
            head = subj[2]
            self.create_object_if_needed(head)
            # setattr(getattr(self, head), adj, obj[0])
            self[head][adj] = obj[0]

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
