#!/usr/bin/env python
"""
Maybies -- A substitute for a boolean that can't be used in "if", "and", "or".

    Copyright (c) 2013 Steve Witham All rights reserved.  
    Constrainer is available under a BSD license, whose full text is at
        https://github.com/switham/constrainer/blob/master/LICENSE
"""

class Maybies(object):
    def __repr__(self):
        return "Maybe"

    def __nonzero__(self):
        raise TypeError("Can't treat Maybies like booleans.")


Maybe = Maybies()


if __name__ == "__main__":
    b = Maybe
    print "b =", b
    if b:
        print "b is true."
    else:
        print "b is false."
