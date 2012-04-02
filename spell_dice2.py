#!/usr/bin/env python
"""
Spell a given word using letter dice.
This time using constrainer.py instead of state2D.py.
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
    letter_cers = {}
    for letter in letters:
        # There are exactly as many dice showing a letter
        # as appearances of the letter in the word.
        min_True = max_True = sum(c == letter for c in word)
        letter_cers[letter] = BoolCer(state, min_True=min_True,
                                             max_True=max_True, letter=letter)

    for i, die in enumerate(dice):
        if not any(letter in die.faces for letter in letters):
            print "Die", die, "is not usable."
            dice.pop(i)
    if len(dice) == len(word):
        # If there are just enough dice, each die is used exactly once.
        min_True, max_True = 1, 1
    elif len(dice) > len(word):
        # If more than enough dice, each die is either not used or used once.
        min_True, max_True = 0, 1
        # (Hmm, this means I could have a cee per die meaning "not used,"
        # and a constraint saying len(word) dice are used.  Then how do I
        # constrain things so that, if a die is used, it's used in at least
        # one place?  Oh of course: exactly one of: "not used," "used for this,"
        # "used for that," etc.)
    else:
        raise Exception("Not enough dice to spell the word!")
        
    die_cers = dict( (die, BoolCer(state, min_True=min_True,
                                          max_True=max_True, die=die))
                     for die in dice)
    for letter in letters:
        for die in dice:
            # The basic variable says: this die is used to show this letter.
            die_shows_letter = BoolCee(state, die=die, letter=letter)
            letter_cers[letter].constrain(die_shows_letter)
            die_cers[die].constrain(die_shows_letter)
            if letter not in die.faces:
                die_shows_letter.set(False)
        
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
            for cee in letter_cers[letter].cees:
                if cee.value == Maybe:
                    print cee.letter, cee.die, "Maybe??"
                    print cee.letter, "cers:"
                    print [c2.value for c2 in letter_cers[cee.letter].cees]
                    print cee.die, "cers:"
                    print [c2.value for c2 in die_cers[cee.die].cees]
                if cee.value:
                    letter_dice[letter].append(cee.die)
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
