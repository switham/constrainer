#!/usr/bin/env python
"""\
boggle.py -- Play Boggle.
"""

from random import *
from sys import argv

DICTIONARY_FILE = "/fs/etc/words.boggle"
DICTIONARY_FILE = "/fs/etc/words"
DICE_FILE = "boggle_dice4.sort"


def extend_the_paths( paths, neighbors ):
    """ Generate paths that are one step longer than the given paths. """
    for path in paths:
        for c in neighbors[ path[-1] ]:
            if not c in path:
                yield path + c


def meet_the_neighbors( rows, cols, squares ):
    """ Return a dictionary of a list of neighbors for each square. """
    neighbors = dict( (s,[]) for s in squares )
    for i, row in enumerate( rows ):
        for j, square in enumerate( row ):
            for nearby_row in rows[ max(0, i-1) : min(i+2,len(rows)) ]:
                for neighbor in nearby_row[ max(0, j-1) : min(j+2,len(cols)) ]:
                    if square != neighbor:
                        neighbors[ square ].append( neighbor )
    return neighbors


def walk_the_paths( squares, neighbors, minlen, maxlen ):
    """ Return list of possible paths where minlen <= length <= maxlen. """
    new_paths = squares
    paths = []
    while len( new_paths[0] ) <= maxlen:
        if len( new_paths[0] ) >= minlen:
            paths += new_paths
        new_paths = list( extend_the_paths( new_paths, neighbors ) )
    return paths


def read_the_dice(filename):
    return list(line.rstrip().split(" ", 1)[0] for line in open(filename))


def roll_the_dice( dice, squares ):
    """ Return a dictionary of a die face for each square. """
    shuffle( dice )
    return dict( (square, choice(die)) for square,die in zip(squares,dice) )


def print_roll( roll, rows ):
    for row in rows:
        for square in row:
            print roll[ square ]+" ",
        print
    

def setup():
    global rows, cols, squares, paths, all_words, DICE

    DICE = read_the_dice(DICE_FILE)
    rows = [ "0123", "4567", "89AB", "CDEF" ]
    cols = zip( *rows )
    squares = ''.join( rows )
    neighbors = meet_the_neighbors( rows, cols, squares )
    paths = walk_the_paths( squares, neighbors, 3, 9 )
    all_words = set( line.rstrip() for line in open( DICTIONARY_FILE ) )


def solve( paths, all_words, roll ):
    table = [ chr(i) for i in range(256) ]
    for square, letter in roll.iteritems():
        table[ ord(square) ] = letter
    table = "".join( table )
    maybe_words = set( path.translate(table) for path in paths )
    return maybe_words.intersection( all_words )


def cmplen(a, b):
    return cmp(len(a), len(b))


def main():
    if len(argv) > 1:
        DICE_FILE = argv[1]
        
    setup()
    while True:
        roll = roll_the_dice( DICE, squares )
        print_roll( roll, rows )
        print
        print sorted(solve(paths, all_words, roll), cmplen)
        print


if __name__ == "__main__":
    main()
