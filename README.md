## Constrainer README

Constrainer is a Python module for solving problems expressed as 
constraints between boolean variables.  It works by deducing variable
values when it can, and guessing (creating tree-search branches) only
when there are no deductions avaiable.

The examples directory contains a variety of puzzle solvers.

Copyright (c) 2013, 2014 Steve Witham All rights reserved.  
Constrainer is available under a BSD license, whose full text is at
    https://github.com/switham/constrainer/blob/master/LICENSE

### Installing

Constrainer doesn't yet have an installer.  But it's pure Python, so...

Download and unpack the latest release:

    curl -L https://github.com/switham/constrainer/archive/v0.5.tar.gz \
        >v0.5.tar.gz
    tar xzf v0.5.tar.gz

This will create a directory constrainer-0.5.  Add the absolute path of
constrainer-0.5 to your PYTHONPATH environment variable.

    export PYTHONPATH="$PYTHONPATH:/my/location/constrainer-0.5"

### Quick Start

Here's a simple program using constrainer to generate combinations out of
a set...

    #!/usr/bin/env python
    from constrainer import *

    state = State()

    vars = [BoolVar(state, name=n) for n in ["amy", "joe", "sue", "bob"]]

    # Constrain so that between two and three of the variables must be true.
    c =  BoolConstraint(state, *vars, min_True=2, max_True=3)

    for is_solution in state.generate_leaves():
        print [var.name for var in c[True]]

...which prints:

    ['bob', 'amy']
    ['sue', 'amy']
    ['sue', 'bob']
    ['sue', 'bob', 'amy']
    ['joe', 'amy']
    ['joe', 'bob']
    ['joe', 'bob', 'amy']
    ['joe', 'sue']
    ['joe', 'sue', 'amy']
    ['joe', 'sue', 'bob']

An expanded version of this demo is in the file 
examples/constrainer_demo.py.

### CONTENTS

    intro
    Installing
    Quick Start
    Contents
    Objects and Initialization
        State
        BoolVar
        BoolConstraint
    Generating Solutions    
        Values of Variables at Solutions
        Single or Multiple Solutions
        Why Generate Non-Solutions?
        Search Depth
        Deterministic Inferences vs. Guessing Strategy
    Setup Patterns
        Small Numbers, Sets, Enums
        Criss-crossing constraints
        Detecting whether one of N
        Other values of min_True and max_True
        Boolean Operations  
    Demos and Support Code

### Objects and Initialization

There are three classes to know about: State, BoolVar and BoolConstraint.

#### State

A State ties together the problem description.   Before doing anything 
else you must create one.  The state must be given when creating any 
BoolVar or BoolConstraint.

    from constrainer import *
    state = State()

The state also contains the generate_leaves() method which carries out
the problem-solving process as described in "Generating Solutions."

#### BoolVar

A BoolVar is a True or False variable whose value is to be solved for.
(It's not a Python variable although it has a value; it's an object used
in the solving process and for reporting back results.)
BoolVar is (currently) the only kind of variable; using them to represent
more interesting situations is discussed in "Setup Patterns," below.  
BoolVars can be given arbitrary attributes to identify them and/or tie 
them to objects within your application.

    >>> fred = BoolVar(state, ssn=1, moniker="fred", obj=my_object1)
    >>> fred.ssn
    1

#### BoolConstraint

A BoolConstraint expresses a requirement on a subset of your variables.
Constraints serve three purposes:

*  They express in a declarative way what must be true in a valid
   solution to your problem.

*  They let the solver deduce the values of some variables from other
   variables they are constrained with.  This can lead to chains of
   deductions without having to search through alternatives.

*  They let the solver decide whether the problem is unsolved, solved,
   or in conflict.  Conflict means that variables have been set in a
   way that violates one or more of the constraints, meaning a dead
   end from which the solver must backtrack.

You can specify variables when creating the constraint, or tie variables
to a constraint after it's created, or both:

    fred = BoolVar(state, ssn=1, moniker="fred", obj=my_object1)
    mark = BoolVar(state, ssn=2, moniker="mark", obj=my_object2)
    john = BoolVar(state, ssn=3, moniker="john", obj=my_object3)
    c = BoolConstraint(state, fred, mark, min_True=1, max_True=1)
    c.constrain(john)

If you have a list of variables, you can constrain them like this:

    stooges = [fred, mark, john]
    c = BoolConstraint(state, *stooges, min_True=1, max_True=1)

or like this:

    c = BoolConstraint(state, min_True=1, max_True=1)
    c.constrain(*stooges)

BoolConstraint is (currently) the only kind of constraint, and its
min_True and max_True attributes specify its complete range of conditions.

Using constraints to describe problems is covered in "Setup Patterns."

### Generating Solutions

When the problem variables and constraints are first set up, all the 
variables are set to a value called Maybe, corresponding to an unfilled
blank.  The solution process replaces Maybies with definite True or False 
values, whether through deduction or by guessing.  A leaf of the search 
tree is reached when either a contradiction is found, or all the blanks 
are filled without contradiction.

Don't try to set BoolVar variables "manually".  You can constrain 
individual variables to fixed values (those constraints will take 
effect once the solving process begins).  Also, once the search begins,
constrainer can't handle having variables or constraints added or
modified.

To look for a solution or solutions, call the State.generate_leaves()    
method.  It's a generator, and the easiest way to use it is with a 
for-loop:

    for is_solution in state.generate_leaves():
        if is_solution:
            print "I found a solution."
        else:
            print "I hit a conflict."
    print "I have run out of possibilities."

#### Values of Variables at Solutions

state.generate_leaves() only yields True when a True or False value has 
been given to every BoolVar associated with state.  If you know what 
BoolVar you're interested in, you can access its ".value" attribute, or 
use it in an if-statement:

    in_the_study = BoolVar(state, ...)
    with_a_rope = BoolVar(state, ...)
    ...
    for is_solution in state.generate_leaves():
        if is_solution:
            if in_the_study:
                if with_a_rope.value == True:
                    print "But there's no chandelier there!"

Lists of those variables connected to a certain constraint
that are True, or those that are False, are available through the
constraint object:

    ...
    suspects = [BoolVar(state, name=n) for n in ["Mr. Bonzini", ...]]
    who_dunnit = BoolConstraint(state, *suspects, min_True=1, max_True=1)
    ....
    for is_solution in state.generate_leaves():
        if is_solution:
            who = who_dunnit[True]
            print who[0].name, "did it!"
            innocents = [var.name for var in who_dunnit[False]]
            print "These people didn't do it:", innocents

#### Single or Multiple Solutions

If you're only interested in one solution, then it's fine to leave the
loop once you've found it.  If you want to know whether it is the *only*
solution, you have to let the loop continue.  If you do, though,
generate_leaves() will modify variables in its search and eventually set
them all back to Maybe, so you will need to save or output any solution
details you need before you continue in the loop.

#### Why Generate Non-Solutions?

generate_leaves() yields a False whenever it gets into a conflict.  The
reason there's an output in that situation is that in my programs I want
to count the dead ends as a measure of how hard problems are or how good
guessing strategies (see below) are for a problem.  In any dead end you 
can look at variable values just as with solutions, except there will 
typically be some Maybe values.  You can get the c[Maybe] list for any
constraint c.

#### Search Depth

At any solution or dead end, the State.depth() method gives an idea how
deep in the search tree you are--how many guesses have been made.  This
number is currently skewed: every left branch increases the depth by 2
and every right branch by 1.

#### Deterministic Inferences vs. Guessing Strategy

The idea of constraint-based problem solving is to deduce as many 
variables' values as possible before resorting to a guess.  Direct 
inference is done by the constraints themselves: each constraint "watches" 
its variables being set and can recognize a contradiction to its rule (too 
many False's or too many True's) or a situation where the rule dictates
how blank variables must be filled.  Filling in those variables can in turn 
wake up other constraints, and so on.

The cascade of direct inferences from a given state is fixed by the 
constraints.  Either there is a contradiction, or a certain set of blanks 
will be filled in in a certain way.  Once inferences have gone as far as
they can, if there are still Maybies, the system needs to try alternatives,
which requires a way to guess.  The current default
strategy is to pick an arbitrary Maybe variable (say v) and make a branch
in the search with v = False on the first, left side.  You can change that 
with the default_guess parameter... or customize the code by sublclassing 
the State class and overriding its guess() method.  The value of v on the
right side of the branch is always the opposite of what was guessed on the
left.
    
### Setup Patterns

Here are some possibilities these simple tools can represent.  You will
find more ideas in the demos included.

#### Small Numbers, Sets, Enums

Given only Boolean variables, we can represent choices out of small sets.
Create a BoolVar for each value or choice, and constrain the set so that 
exactly one is True:

    x_values = []
    for i in range(10):
        name = "digit_is_%d" % i
        x_values.append(BoolVar(state, name=name))
    x_c = BoolConstraint(state, *x_values, min_True=1, max_True=1)

This has the effect that if one of the x_values becomes True, the rest all
become False, or if all but one become False, the last one becomes True.

#### Criss-crossing constraints

Usually every variable is under more than one constraint.  For instance, in
the eight queens problem, there is one queen in each row, one queen in each
column, and at most one--i.e. zero or one--queen in each upward-slanting 
and each downward-slanting diagonal.  Here we create one BoolVar for each
square, collect them into appropriate subsets, and constrain the subsets:

    cols = [[] for x in range(8)]
    rows = [[] for y in range(8)]
    up_diags = [[] for ud in range(15)]
    dn_diags = [[] for dd in range(15)]
    for x in range(8):
        for y in range(8):
            square = BoolVar(state, x=x, y=y)
            cols[x].append(square)
            rows[y].append(square)
            up_diags[x + y].append(square)
            dn_diags[x - y + 7].append(square)
    for row_or_col in rows + cols:
        BoolConstraint(state, *row_or_col, min_True=1, max_True=1)
    for diag in up_diags + dn_diags:
        BoolConstraint(state, *diag, min_True=0, max_True=1)

#### Detecting whether one of N

Since not all diagonals are occupied, we might want a variable to stand for
whether a given diagonal is occupied.  We can do this with a "not-occupied"
variable and replacing the "zero or one" constraint with a constraint that
exactly one of (all the squares in the diagonal plus "not-occupied") is
true:

    n_o = BoolVar(state, name="diag_not_occupied")
    BoolConstraint(state, *(diag + [n_o]), min_True=1, max_True=1)

For a set of sets, each with a "not-occupied" variable, you can then 
constrain the number of sets that are occupied (see "Other Values..."
next).

If you really need a variable that is true, rather than false, if one of a
set is true, see NOT under "Boolean Operations," below.

#### Other values of min_True and max_True
        
So far, the only values for min_True and max_True have been zero and one.
An example where other values are used is the demo "spell_dice.py" included
here.  spell_dice.py takes a set of dice with letters on their faces, and 
tries to spell a phrase.  There are BoolVars for 

    "This die has this letter showing," 

and constraints for 

    "This die has just one letter showing."
 
Now imagine a phrase with three E's in it, and imagine that five of our 
dice have E on one face.   Then the program sets up a constraint that

    "Exactly three of these five dice have E showing."

That reduces redundancy in both the results and the search, by not 
swapping the E's around pointlessly between places in the phrase.

Other combinations (say out of a set of N BoolVars):

    min_True=1, max_True=N      at least one is True
    min_True=N-1, max_True=N-1  exactly one is False
    min_True=N-1, max_True=N    at most one is False
    min_True=0, max_True=N-1    at least one is False
    min_True=1, max_True=N-1    neither all are True nor all False

#### Boolean Operations  

The representational methods so far are good enough for the soma.py and
spelldice.py examples included with constrainer.  But BoolConstraints and 
BoolVars can implement the complete set of Boolean operations (and, or, 
not...) in arbitrarily complex arrangements.

It's worth noting first that in general 
constraints express relations, not just functions.  A relation
between variables A and B can allow more than one value of A for a given
B and vice versa.  Also, even when a constraint expresses a function,
and unlike logic functions in most computer languages or digital 
circuitry, constraints don't have dedicated inputs and outputs; 
information can flow in any direction that's a logical inference from the
known variables and constraints.

A simple relation is the "implies" relationship:

    not(A) implies B
        BoolConstraint(state, A, B, min_True=1, max_True=2)

This constraint also means, "Not(B) implies A," and "A or B or both."
Note that if A is true, B can be true or false, and if B is true, A
can be true or false.  They just can't both be false.

The NOT function is one-to-one, which means each of the variables is
completely determined by the other:

    A = not(B):
        BoolConstraint(state, A, B, min_True=1, max_True=1)

(This also means, "A or B but not both," and "B = not(A).")  Here's
the NAND relation:

    C = NAND(a, b) = not(A and B):
        BoolConstraint(state, C, A, B, min_True=0, max_True=2)
        BoolConstraint(state, C, A, min_True=1, max_True=2)
        BoolConstraint(state, C, B, min_True=1, max_True=2)

With NAND, C is completely determined by A and B, but neither A nor B is 
completely determined by the other two.

With NOT and NAND and enough extra variables you can build any Boolean
function, starting with AND and OR...

    A and B = not(NAND(A, B))
    A or B = NAND(not(A), not(B))

### Demos and Support Code

The constrainer project contains these interesting things (and more):

    constrainer/ddict.py
        An enhanced version of the standard Python collections.defaultdict
        class.

    constrainer/maybies.py
        Defines the Maybe placeholder value and its behavior.

    examples/spell_dice.py
        Given a set of dice with letters on their faces, use the dice to
        spell a given phrase.

    examples/boggle_dice4.sort
    examples/boggle_dice5.sort
    examples/kitchen_dice.sort
        Three different sets of letter dice.

    examples/soma.py
        Piet Hein's Soma puzzle: Given descriptions of some 3D puzzle piece 
        shapes, and of a desired shape, find ways to build the shape out of 
        the pieces.
    examples/soma_puzzles/
        soma_pieces.spc
            Shapes of the standard Soma puzzle pieces.
        *.spz
            Puzzles for the standard Soma pieces.  Not all have solutions.
    examples/rotated_piece_pix.txt
    examples/cube.rtf
        Typewriter pictures of Soma pieces rotated every which way.
        Generated by shape_to_pic() and friends inside soma.py.
            
-fin-
