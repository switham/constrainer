#!/usr/bin/env python
"""
examples/sortdice.py -- Put description of a set of dice in canonical form.
abcdef comment
ghijkl comment comment etc
with both letters in die (first field) and lines sorted alphabetically.
    Copyright (c) 2013 Steve Witham All rights reserved.  
    Constrainer is available under a BSD license, whose full text is at
        https://github.com/switham/constrainer/blob/master/LICENSE
"""

from sys import stdin


def fixline(line):
    fields = line.split(' ', 1)
    die = fields[0]
    assert len(die) == 6, "Not six faces: " + repr(line)
    die = "".join(sorted(side for side in die))
    return ' '.join([die] + fields[1:])


def main():
    for line in sorted(fixline(line.rstrip()) for line in stdin):
        print line

if __name__ == "__main__":
    main()
    
