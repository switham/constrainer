#!/usr/bin/env python
"""\
boggle.py --
"""

import random
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='Generate and solve 4 x 4 Boggle boards.')
    parser.add_argument("--words",
        type=str, default="/fs/etc/words.boggle",
        help="name of file of usable words "
             "(default /fs/etc/words.boggle)")
    parser.add_argument("--dice",
        type=str, default="boggle_dice4.sort",
        help="name of file of descriptions of dice "
             "(default boggle_dice4.sort)")
    parser.add_argument("--minlen",
        type=int, default=3,
        help="minimum length of words to find (default 3)")
    parser.add_argument("--maxlen",
        type=int, default=9,
        help="maximum length of words to find (default 9)")
    args = parser.parse_args()
    setup(args)
    while True:
        roll = roll_the_dice(dice, squares)
        print_roll(roll, rows)
        print
        print sorted(solve(paths, all_words, roll),
                     lambda a, b: cmp(len(a), len(b)))
        print


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


def extend_the_paths( paths, neighbors ):
    """ Generate paths that are one step longer than the given paths. """
    for path in paths:
        for c in neighbors[ path[-1] ]:
            if c not in path:
                yield path + c


def walk_the_paths(squares, neighbors, minlen, maxlen):
    """ Return list of possible paths where minlen <= length <= maxlen. """
    new_paths = squares
    paths = []
    while len(new_paths[0]) <= maxlen:
        if len(new_paths[0]) >= minlen:
            paths += new_paths
        new_paths = list(extend_the_paths( new_paths, neighbors))
    return paths


def roll_the_dice(dice, squares):
    """ Return a dictionary of a die face for each square. """
    random.shuffle(dice)
    return dict((square, random.choice(die))
                for square, die in zip(squares,dice))


def print_roll(roll, rows):
    for row in rows:
        print "  ".join(roll[square] for square in row)
    

def setup(args):
    global rows, cols, squares, paths, all_words, dice

    dice = list(line.rstrip().split(" ", 1)[0] for line in open(args.dice))
    rows = [ "0123", "4567", "89AB", "CDEF" ]
    cols = zip(*rows)
    squares = ''.join(rows)
    neighbors = meet_the_neighbors(rows, cols, squares)
    paths = walk_the_paths(squares, neighbors, args.minlen, args.maxlen)
    all_words = set(line.rstrip().replace("qu", "q")
                    for line in open(args.words))


def solve(paths, all_words, roll):
    table = [chr(i) for i in range(256)]
    for square, letter in roll.iteritems():
        table[ord(square)] = letter
    table = "".join(table)
    maybe_words = set(path.translate(table) for path in paths)
    match_words = maybe_words.intersection(all_words)
    return [word.replace("q", "qu") for word in match_words]


if __name__ == "__main__":
    main()
