from .core import Talk


def main():
    print("TALK")
    t = Talk(print_mode=True)
    line = ''
    while line != 'quit':
        line = input()
        t.talk(line)
    print("THANKS BYE")
