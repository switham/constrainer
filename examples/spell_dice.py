#!/usr/bin/env python
""" examples/spell_dice.py -- Spell a given word or phrase using letter dice.
    Copyright (c) 2013 Steve Witham All rights reserved.  
    Constrainer is available under a BSD license, whose full text is at
        https://github.com/switham/constrainer/blob/master/LICENSE
"""

import sys
import argparse

from constrainer import *
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
    state = State(verbose=verbose)
    
    letters = list(set(word))
    for i, die in enumerate(dice):
        if not any(letter in die.faces for letter in letters):
            print "Die", die, "is not usable."
            dice.pop(i)
    if len(dice) < len(word):
        raise Exception("Not enough dice to spell the word!")

    # First we set up the Constrainers:

    letter_constraints = {}
    for letter in letters:
        # There are exactly as many dice showing a letter
        # as appearances of the letter in the word.
        n_appears = sum(c == letter for c in word)
        letter_constraints[letter] = BoolConstraint(state, min_True=n_appears,
                                             max_True=n_appears, letter=letter)

    # It helps here to treat unused dice as like being
    # "used for nothing," or "showing the null letter."
    # The number of unused dice is exactly as many as the word doesn't need:
    n_unused_dice = len(dice) - len(word)
    letter_constraints["unused"] = BoolConstraint(state,
                                                  min_True=n_unused_dice,
                                                  max_True=n_unused_dice,
                                                  letter="unused")

    # Each die is used exactly once: either to show a letter, or for nothing:
    die_constraints = dict( (die, BoolConstraint(state, min_True=1, max_True=1,
                                                 die=die))
                            for die in dice)

    # Now the Variables:
    
    for letter in letters + ["unused"]:
        for die in dice:
            # Variables to say: this die is used to show this letter
            # (or, this die is not used).
            if letter == "unused" or letter in die.faces:
                die_shows_letter = BoolVar(state, die=die, letter=letter)
                letter_constraints[letter].constrain(die_shows_letter)
                die_constraints[die].constrain(die_shows_letter)
        
    n_solutions = 0
    n_deadends = 0
    for is_solution in state.generate_leaves(verbose):
        if not is_solution:
            n_deadends += 1
            continue

        n_solutions += 1
        if verbose:
            print "===== solution", n_solutions, state.depth(), "====="
            sys.stdout.flush()
        if just_count:
            continue

        # Show a solution.
        # For each letter, make a list of dice that are showing it.
        letter_dice = dict( (letter, []) for letter in letters)
        for letter in letters:
            for var in letter_constraints[letter].vars:
                if var.value == Maybe:
                    print var.letter, var.die, "Maybe??"
                    print var.letter, "constraints:"
                    print [c2.value \
                           for c2 in letter_constraints[var.letter].vars]
                    print var.die, "constraints:"
                    print [c2.value for c2 in die_constraints[var.die].vars]
                if var.value:
                    letter_dice[letter].append(var.die)
        # Remove dice from their lists as you use them to spell:
        for letter in word:
            die = letter_dice[letter].pop()
            print letter, die
        print
        if not multi:
            break
        
    return n_solutions, n_deadends


if __name__ == "__main__":
    args = parse_args()
    dice = [Die(line) for line in open(args.dice)]
    n_solutions, n_deadends = spell(args.word, dice,
                                    args.many, args.count, args.verbose)
    if args.count or args.many:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
    print n_deadends, "dead ends"
    if n_solutions == 0:
        sys.exit(1)
