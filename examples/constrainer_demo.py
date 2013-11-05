#!/usr/bin/env python
""" 
examples/constrainer_demo.py 

    Copyright (c) 2013 Steve Witham All rights reserved.  
    Constrainer is available under a BSD license, whose full text is at
        http://github.com/switham/constrainer/blob/master/LICENSE
"""

from constrainer import *
import sys


def demo(verbose=False, default_guess=None):
    state = State(verbose=verbose)

    vars = [BoolVar(state, name=n) for n in ["amy", "joe", "sue", "bob"]]

    # Constrain so that between two and three of the variables must be true.
    c =  BoolConstraint(state, *vars, min_True=2, max_True=3)

    for is_solution in state.generate_leaves(verbose=verbose, 
                                             default_guess=default_guess):
        print "Depth:", state.depth()
        print [var.name for var in c[True]]
        print dict((var.name, var.value) for var in vars)
        print


if __name__ == "__main__":
    verbose = False
    default_guess = True
    i = 1
    try:
        while i < len(sys.argv): 
            if sys.argv[i] == "--verbose":
                verbose = True
                i += 1
            elif sys.argv[i] == "--default_guess":
                default_guess = bool(sys.argv[i + 1])
                i += 2
            else:
                raise Exception("usage")
    except:
        print >>sys.stderr, "Usage:", sys.argv[0], "[options...]"
        print >>sys.stderr, "    --verbose"
        print >>sys.stderr, "    --default_guess True|False"
        sys.exit(1)

    demo(verbose, default_guess)
