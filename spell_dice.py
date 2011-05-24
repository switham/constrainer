#!/usr/bin/env python
"""
Spell a given word using letter dice.
"""

import random
import sys
import argparse
import collections


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


class Maybies(object):
    def __repr__(self):
        return "Maybe"

    def __nonzero__(self):
        raise TypeError("Can't treat Maybies like booleans.")

Maybe = Maybies()


class State(list):
    def __init__(self, iterator):
        for row in iterator:
            self.append(row)
        self.log_stack = []
        self.rows = []
        self.cols = []

    def set(self, row, col, new_y):
        """ Setting doesn't adjust the rows' and columns' counts. """
        self.log_stack[-1].append((row, col, self[row][col]))
        self[row][col] = new_y

    def rewind(self):
        """ Rewinding doesn't adjust the rows' and columns' counts. """
        for row, col, popped_y in reversed(self.log_stack.pop()):
            self[row][col] = popped_y
        

class StateRowOrCol(object):
    def __init__(self, state, r0, c0, dr, dc, min_True, max_True):
        self.state = state
        self.r0, self.c0 = r0, c0
        self.dr, self.dc = dr, dc
        self.min_True, self.max_True = min_True, max_True
        #
        self.len = len(state) * dr + len(state[0]) * dc
        self.recount()

    def row_col(self, i):
        return self.r0 + i * self.dr, self.c0 + i * self.dc
    
    def __len__(self):
        return self.len

    def __getitem__(self, x):
        r, c = self.row_col(x)
        return self.state[r][c]
        
    def __setitem__(self, x, new_y):
        r, c = self.row_col(x)
        self.state.set(r, c, new_y)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def recount(self):
        self._n_True = sum(x == True for x in self)
        self._n_Maybe = sum(x == Maybe for x in self)

    def n_True(self): return self._n_True

    def n_Maybe(self): return self._n_Maybe

    def freedom(self):
        return self.n_Maybe() + self.n_True() - self.min_True


class Done(Exception):
    pass


def spell(word, dice, multi=False, just_count=False, verbose=False):
    letters = list(set(word))
    state = State([(letter in die.faces and Maybe) for letter in letters] for die in dice)
    state.cols = []
    for j, letter in enumerate(letters):
        min_True = max_True = sum(c == letter for c in word)
        state.cols.append(StateRowOrCol(state, 0, j, 1, 0, min_True, max_True))
    if len(dice) == len(word):
        min_True, max_True = 1, 1
    else:
        min_True, max_True = 0, 1
    state.rows = []
    for i, die in enumerate(dice):
        state.rows.append(StateRowOrCol(state, i, 0, 0, 1, min_True, max_True))
    state.n_solutions = 0
    
    def report_solution():
        state.n_solutions += 1
        if verbose: print "===== solution", state.n_solutions, len(state.log_stack), "====="
        if just_count:
            return

        letter_dice = dict( (letter, [die for i, die in enumerate(dice) if state[i][j] == True])
                           for j, letter in enumerate(letters))
        for letter in word:
            die = letter_dice[letter].pop()
            print letter, die
        print
        
    try:
        spell_more(state, multi, report_solution, verbose)
    except Done:
        pass
    return state.n_solutions


class Stuck(Exception):
    pass


def massage_rows_or_cols(rcs, verbose):
    """
    Scan rows or columns, drawing conclusions that are certain.
    Does not recount the perpendicular cols/rows.
    If we're stuck, raise the Stuck exception.
    """
    for rc in rcs:
        rc.recount()
        if rc.n_True() + rc.n_Maybe() < rc.min_True or rc.n_True() > rc.max_True:
            raise Stuck()

        if rc.n_True() == rc.max_True and rc.n_Maybe() > 0:
            for i in range(len(rc)):
                if rc[i] == Maybe:
                    if verbose: print "inferred", rc.row_col(i), False
                    rc[i] = False
            rc.recount()
        if rc.n_Maybe() > 0 and rc.n_True() + rc.n_Maybe() == rc.min_True:
            for i in range(len(rc)):
                if rc[i] == Maybe:
                    if verbose: print "inferred", rc.row_col(i), True
                    rc[i] = True
            rc.recount()


def spell_more(state, multi, report_solution_fn, verbose):
    state.log_stack.append([])

    prev_len = -1
    while len(state.log_stack[-1]) > prev_len:
        prev_len = len(state.log_stack[-1])
        try:
            massage_rows_or_cols(state.rows, verbose)
            massage_rows_or_cols(state.cols, verbose)
        except Stuck:
            state.rewind()
            return

    if sum(row.n_Maybe() for row in state.rows) == 0:
        report_solution_fn()
        if multi:
            state.rewind()
            return
        else:
            raise Done()

    # Now all certain moves have been made above.  Pick the move with the least "freedom".

    f, i, j = min((row.freedom() * col.freedom(), i, j)
                  for i, row in enumerate(state.rows) for j, col in enumerate(state.cols)
                  if state[i][j] == Maybe)
    for tf in False, True:
        if verbose: print "try", i, j, tf
        state.set(i, j, tf)
        spell_more(state, multi, report_solution_fn, verbose)
        if verbose: print "===== pop", len(state.log_stack), "====="
    state.rewind()
    return



if __name__ == "__main__":
    args = parse_args()
    dice = [Die(line) for line in open(args.dice)]
    n_solutions = spell(args.word, dice, args.many, args.count, args.verbose)
    if args.count:
        print n_solutions
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
        sys.exit(1)
