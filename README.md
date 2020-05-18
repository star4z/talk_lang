Terminology of project still needs to be established. For example, the linguistics term object and the OOP term
object are both used in the project. (When splitting a sentence, the object is called the obj and a class object of
an undefined class reports its class as "object".)

All nouns should retain their original formatting as much as possible under the hood in order to maintain meaning,
including capitalization. For a somewhat contrived example, "My destiny awaits me in the parlor." vs "My Destiny
awaits me in the parlor." could have very different meanings: One's future awaits them in the parlor, or their 
sweetheart. A better example: "The bill is not yet approved." and "Bill is not yet approved." Assuming these were 
the only statements in the current session, or memory, they would both result in `self.bill.approved = false` or 
something like that, but if we respect formatting, we get `self.bill.approved = false` and `self.Bill.approved = false`,
which preserves the speaker's intent.
As adjective functionality has not yet been added, it is difficult to determine whether a use case for spaces would
be necessary, but type("this thing", () {}) is valid Python (as of yet).

"Ben is a person. Ben is tall, skinny, and nerdy. What is Ben?" -> "Ben is a tall, skinny, nerdy person."

"Ben is a Person with a height of 6ft. Tall people have a height over 6ft. Is Ben tall?" -> "Yes."