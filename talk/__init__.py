# END_LINES = '[.?\n]'

END_LINES = ('.', '?')

A = 'a'  # nonspecific article
AN = 'an'
THE = 'the'  # specific article
articles = (A, AN, THE)

IS = 'is'
ARE = 'are'
HAS = 'has'

verbs = (IS, ARE, HAS)

WHAT = 'what'  # query operator

OF = 'of'

# Word classifications
VERB = 'verb'
SUBJECT = 'subj'
OBJECT = 'obj'
ARTICLE = 'article'

# Sentence classifications
DECLARATIVE = 'declarative'
INTERROGATIVE = 'interrogative'


class Talk:
    """
    Main class for Talk lang.
    Can be used by calling Talk("Some sentence") for convenience, and also with .talk("Some sentence") for repeated
    calls.
    """
    def __init__(self, line='', print_mode=False):
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
            if c == '.':
                self.sentence(line[last_end:i], DECLARATIVE)
                last_end = i + 1
            elif c == '?':
                self.sentence(line[last_end:i], INTERROGATIVE)
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
                obj = words[verb_index + 1:]
                obj = [o for o in obj if o not in articles]
                self.handle_verb(obj, subj, verb)
            elif sentence_type == INTERROGATIVE:
                query = words[0].lower()
                if query == WHAT and verb == IS:
                    obj = words[verb_index + 1:]
                    obj = [o for o in obj if o not in articles]
                    if OF in obj and len(obj) == 3:
                        result = getattr(getattr(self, obj[2]), obj[0])
                        self.print(result)
                    else:
                        result = getattr(getattr(self, obj[2]), obj[0])
                        self.print(result)

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
            setattr(getattr(self, subj[0]), obj[0], obj[2])

        # it's a field with no value; eg. obj has a subj
        elif len(obj) == 1 and len(subj) == 1:
            self.create_object_if_needed(subj[0])
            instance = self.create_object_if_needed(obj[0])
            setattr(getattr(self, subj[0]), obj[0], instance)

    def handle_is(self, obj, subj):
        if len(subj) == 1 and len(obj) == 1:
            # it's probably a variable assignment
            class_name = obj[0]
            obj_type = type(class_name, (), {})
            self.classes[class_name] = obj_type
            setattr(self, subj[0], obj_type())

    def create_object_if_needed(self, obj):
        if not hasattr(self, obj):
            # Create generic "object" type and add it to the stored types
            object_type = type('object', (), {})
            self.classes['object'] = object_type
            # Adds subject as an 'object' to this root object
            instance = object_type()
            setattr(self, obj, instance)
            return instance
        else:
            return getattr(self, obj)


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
