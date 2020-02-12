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
    def __init__(self, line='', print_mode=False):
        self.classes = {}
        self.output = ''
        self.print_mode = print_mode

        self.talk(line)

    def talk(self, line):
        # This needs to be improved because the punctuation is helpful for determining sentence structure.
        line = ''.join(line.split('\n'))
        last_end = 0
        for i, c in enumerate(line):
            if c == '.':
                self.sentence(line[last_end:i], DECLARATIVE)
                last_end = i + 1
            elif c == '?':
                self.sentence(line[last_end:i], INTERROGATIVE)
                last_end = i + 1
        pass

    def __str__(self):
        return self.output

    def print(self, line):
        if self.print_mode:
            print(line)
        self.output += str(line) + '\n'

    def sentence(self, sentence, sentence_type):
        words = [word for word in sentence.split(' ') if word]
        verb_index = next((i for i, word in enumerate(words) if word in verbs), None)
        if verb_index:
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

    def handle_verb(self, obj, subj, verb):
        if verb == IS:
            self.handle_is(obj, subj)
        elif verb == HAS:
            self.handle_has(obj, subj)

    def handle_has(self, obj, subj):
        if OF in obj and len(obj) == 3 and len(subj) == 1:
            # it's probably a field assignment
            if not hasattr(self, subj[0]):
                object_type = type('object', (), {})
                self.classes['object'] = object_type
                setattr(self, subj[0], object_type())
            setattr(getattr(self, subj[0]), obj[0], obj[2])

    def handle_is(self, obj, subj):
        if len(subj) == 1 and len(obj) == 1:
            # it's probably a variable assignment
            obj_type = type(obj[0], (), {})
            self.classes[obj[0]] = obj_type
            setattr(self, subj[0], obj_type())


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
