#!/usr/bin/env python
"""
sortdice.py -- Put description of a set of dice in canonical form.
abcdef comment
ghijkl comment comment etc
with both letters in die (first field) and lines sorted alphabetically.
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
    
