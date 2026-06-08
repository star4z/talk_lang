# Talk

Talk is an NLP-ish language designed to look like English.

Talk parses text to determine sentence structure and creates code structures internally to maintain the logic between
them.

In basic usage, Talk will consist of stating data and asking questions in order to produce an output.

Here's an example for calculating the nth Fibonacci number:

```
A dummy uses numbers.
A dummy can calculate.
A dummy requires a number to calculate.
When the dummy calculates, if the number equals 1, then the result is 0.
When the dummy calculates, if the number equals 2, then the result is 1.
When the dummy calculates, if the number is greater than 2, then the result is the sum of calculating (the number minus
1), and calculating (the number minus 2).
The dummy calculates with 8.
What is the result?
```

The expected result is `13`.

Note that the parentheses are needed to specify the difference between foo(a) - b and foo(a - b).

Numbers is a library of Nouns and Verbs to handle basic math with integers and floats. `The dummy uses numbers.` is 
intended as an import statement of this library.

Talk is intended to resemble the text of a book. A Talk program should resemble a list of statements and their conclusions. Talk is not intended to be a conversational partner, and therefore features should not be added where you can talk to Talk directly. You are *making* talk, not *talking to Talk*. Questions should be understood to be rhetorical, and Talk just happens to fill in the blank for your convenience. 

This is why in the examples the dummy is created as an object to do calculations on, instead of doing the calculations directly on the Talk object. Maybe this can be changed in the future to allow nonspecific subjects, like "To foo a number, add 2 to the number."

## Using Talk

### Interactive Terminal

Talk can be run as an interactive terminal using `python3 -m talk`.

If more access to the state is desired, run python interactively. See the API section below. 

### API

Talk can be invoked from a script:

```py
from talk import Talk

result = Talk('This is an example').output
```

To have Talk print answers to the terminal, use `print_mode=True`:

```py
result = Talk('An apple is red.', print_mode=True)
```

`output` will contain the result regardless of whether `print_mode` is enabled.

`Talk().__dict__` can be useful to observe the internal state and better understand how Talk represents concepts internally.

See tests for more examples.

## Supported Language Features

Talk supports a small English-like language for defining objects, state, queries, and simple functions.

- Object creation and typing: `Ben is a person.`
- Property assignment: `Ben has a job.`, `Ben has a height of 6ft.`, and possessive forms like `Ben's height is 6ft.`
- Value queries: `What is the height of Ben?`, `What is Ben's height?`
- Yes/no queries: `Does Ben have a job?`, `Is Ben tall?`
- Unknown answers: unknown values respond with `I don't know.`
- Literal values: numeric literals and quoted strings (`'foo'` / `"foo"`).
- Basic arithmetic in queries: `What is 2 + 2?`, `What is a + b?`, with support for `+`, `-`, `*`, `/`, and parentheses.
- Function/action definitions: `A dummy can calculate.`, `A dummy requires a number to calculate.`, `When the dummy calculates, if ... then ...`, and invocation like `The dummy calculates with 8.`

## Aspirational Language Features

### Formatting-specific nouns

All nouns should retain their original formatting as much as possible under the hood in order to maintain meaning,
including capitalization. For example: "The bill is not yet approved." and "Bill is not yet approved.

"The bill is not yet approved. Is the bill approved?" -> "No"

"The bill is not yet approved. Is Bill aproved?" -> "I don't know."

"Bill is not yet approved. Is the bill approved?" -> "I don't know."

"Bill is not yet approved. Is Bill approved?" -> "No"

Poor Bill, always trying to get approved but never getting approved.

This could be extended to inferring some properties of object type from the formatting. For example, "His destiny awaits him in the parlor." vs "His Destiny
awaits him in the parlor." could have very different meanings: One's future awaits them in the parlor, or their 
sweetheart. Should 

"His destiny awaits him in the parlor. What awaits him in the parlor?" -> "His destiny"

"His destiny awaits him in the parlor. Who awaits him in the parlor?" -> "I don't know"

"His Destiny awaits him in the parlor. What awaits him in the parlor?" -> "I don't know"

"His Destiny awaits him in the parlor. Who awaits him in the parlor?" -> "Destiny"

### Adjective support

"Ben is a person. Ben is tall, skinny, and nerdy. What is Ben?" -> "Ben is a tall, skinny, nerdy person."

### Logical following

"Ben is a Person with a height of 6ft. Tall people have a height over 6ft. Is Ben tall?" -> "Yes."