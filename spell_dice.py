#!/usr/bin/env python
"""
Spell a given word using letter dice.
"""

import sys
import argparse

from state2D import *
from maybies import *


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dice", metavar="file",
        type=str, default="kitchen_dice.sort",
        help="name of file of descriptions of dice ")
    parser.add_argument("--many", "--multi", "-m",
        action="store_true",
        help="generate as many solutions as possible, not just one")
    parser.add_argument("--count", "-c",
        action="store_true",
        help="just output a count of the number of solutions found")
    parser.add_argument("--verbose", "-v",
        action="store_true",
        help="show search progress")
    parser.add_argument("word",
        type=str, help="word to spell out")
    return parser.parse_args()


class Die(object):
    def __init__(self, line):
        parts = line.rstrip().split(None, 1)
        self.faces = parts[0]
        self.comment = (parts[1:] or [""])[0]

    def __str__(self):
        return self.faces + " " + self.comment

    def __repr__(self):
        return "Die(%r)" % str(self)


def spell(word, dice, multi=False, just_count=False, verbose=False):
    letters = list(set(word))
    state = State2D([(Maybe if letter in die.faces else False)
                   for letter in letters]
                  for die in dice)
    state.cols = []
    for j, letter in enumerate(letters):
        min_True = max_True = sum(c == letter for c in word)
        state.cols.append(StateView(state, 0, j, 1, 0, min_True, max_True))
    if len(dice) == len(word):
        min_True, max_True = 1, 1
    else:
        min_True, max_True = 0, 1
    state.rows = []
    for i, die in enumerate(dice):
        state.rows.append(StateView(state, i, 0, 0, 1, min_True, max_True))
        
    n_solutions = 0
    n_deadends = 0
    for tf in generate_spellings(state, verbose):
        if not tf:
            n_deadends += 1
            continue

        n_solutions += 1
        if verbose:
            print "===== solution", n_solutions, state.depth(), "====="
            sys.stdout.flush()
        if just_count:
            continue

        letter_dice = dict( (letter, [die for i, die in enumerate(dice)
                                          if state[i][j] == True])
                           for j, letter in enumerate(letters))
        for letter in word:
            die = letter_dice[letter].pop()
            print letter, die
        print
        if not multi:
            break
        
    return n_solutions, n_deadends


def massage_rows_and_cols(rcs, verbose):
    """
    Scan rows and/or columns, drawing any conclusions that are certain.
    Return whether-stuck, whether-quiet
    """
    quiet = True
    for rc in rcs:
        rc.recount()
        if rc.n_True() + rc.n_Maybe() < rc.min_True \
                or rc.n_True() > rc.max_True:
            return True, True

        if rc.n_Maybe() > 0:
            if rc.n_True() == rc.max_True:
                quiet = False
                rc.set_Maybes(False, verbose)
            elif rc.n_True() + rc.n_Maybe() == rc.min_True:
                quiet = False
                rc.set_Maybes(True, verbose)
    return False, quiet


def most_probable_move(state):
    maybeRows = [(i, row) for i, row in enumerate(state.rows)
                          if row.n_Maybe() > 0]
    maybeCols = [(j, col) for j, col in enumerate(state.cols)
                          if col.n_Maybe() > 0]
    p, i, j, tf = max((row.probability(tf) * col.probability(tf), i, j, tf)
                      for i, row in maybeRows for j, col in maybeCols
                      if state[i][j] == Maybe
                      for tf in [True, False])
    return p, i, j, tf


def generate_spellings(state, verbose):
    state.push()
    while state.depth() > 0:
        quiet = False
        while not quiet:
            stuck, quiet = massage_rows_and_cols(state.rows + state.cols,
                                                 verbose)
        if stuck:
            yield False

        elif sum(row.n_Maybe() for row in state.rows) == 0:
            yield True

        else:
            p, i, j, tf = most_probable_move(state)
            # Here, push the other choice, so that if and when we
            # come back, we'll take the remaining alternative to tf.
            state[i][j] = not tf
            state.push()
            
            if verbose:
                print "try", state.depth(), (i, j), tf, "%f%%" % (100 * p)
                sys.stdout.flush()
            state[i][j] = tf
            continue
        
        state.pop()
        if verbose:
            print "===== pop", state.depth(), "====="
            sys.stdout.flush()


if __name__ == "__main__":
    args = parse_args()
    dice = [Die(line) for line in open(args.dice)]
    n_solutions, n_deadends = spell(args.word, dice,
                                    args.many, args.count, args.verbose)
    if args.count:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
    print n_deadends, "dead ends"
    if n_solutions == 0:
        sys.exit(1)
