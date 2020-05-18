Talk parses text to determine sentence structure and creates code structures internally to maintain the logic between
them.

In basic usage, Talk will consist of stating data and asking questions in order to produce an output.

Here's an example (that may not work yet) for calculating the nth Fibonacci number:

```
A dummy uses numbers.
A dummy can calculate.
A dummy requires a number to calculate.
When the dummy calculates, if the number equals 1, then the result is 0.
When the dummy calculates, if the number equals 2, then the result is 1.
When the dummy calculates, if the number is greater than 2, then the result is the sum of calculating (the number minus
1, and calculating (the number minus 2).
The dummy calculates with 8.
What is the result?
```

The expected result is `13`.

Note that the parentheses are needed to specify the difference between foo(a) - b and foo(a - b).

Numbers is a library of Nouns and Verbs to handle basic math with integers and floats. `The dummy uses numbers.` is 
intended as an import statement of this library.