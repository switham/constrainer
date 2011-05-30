#!/usr/bin/env python
"""
Spell a given word using letter dice.
"""

import sys
import argparse


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
NotCalculatedYet = Maybies()


class State(list):
    def __init__(self, *args):
        super(State, self).__init__(*args)
        self.log_stack = []
        self.rows = []
        self.cols = []

    def set(self, i, j, new_value):
        """ Setting doesn't adjust the rows' and columns' counts. """
        self.log_stack[-1].append((i, j, self[i][j]))
        self[i][j] = new_value

    def rewind(self):
        """ Rewinding doesn't adjust the rows' and columns' counts. """
        for i, j, popped_value in reversed(self.log_stack.pop()):
            self[i][j] = popped_value
        

def choose_range(n, j, k):
    """
    How many subsets of between j and k out of n things are there?
    Like sum(choose(n, i) for i in range(j, k + 1)) but faster.
    """
    if k < j:  return 0
    assert 0 <= j and k <= n
    term = 1
    t = 0
    for i in range(k):
        if i >= j:  t += term
        term = term * (n - i) / (i + 1)
    return t + term


class StateRowOrCol(object):
    def __init__(self, state, r0, c0, dr, dc, min_True, max_True):
        self.state = state
        self.r0, self.c0 = r0, c0
        self.dr, self.dc = dr, dc
        self.min_True, self.max_True = min_True, max_True
        self.len = len(state) * dr + len(state[0]) * dc
        self._combos = [NotCalculatedYet, NotCalculatedYet]
        self.recount()

    def row_col(self, k): return self.r0 + k * self.dr, self.c0 + k * self.dc
    
    def __len__(self): return self.len

    def __getitem__(self, k):
        i, j = self.row_col(k)
        return self.state[i][j]
        
    def __setitem__(self, k, new_value):
        i, j = self.row_col(k)
        self.state.set(i, j, new_value)
        self._combos[False] = self._combos[True] = NotCalculatedYet

    def __iter__(self): return (self[k] for k in range(len(self)))

    def recount(self):
        self._n_True = sum(value == True for value in self)
        self._n_Maybe = sum(value == Maybe for value in self)

    def n_True(self): return self._n_True

    def n_Maybe(self): return self._n_Maybe

    def probability(self, tf):
        """
        Guess probability that a solution exists in which a random Maybe is be set to tf.
        Actually, assume there is exactly ONE solution, and guess the probability
        that one of the Maybes in this row or column is tf in the solution.
        """
        if self._combos[tf] == NotCalculatedYet:
            # How many ways of filling in would be left if one Maybe were set to True?  To False?
            assert self.n_Maybe() > 0
            suppose_Maybe = self.n_Maybe() - 1
            for b in True, False:
                suppose_True = self.n_True() + b
                min_Maybe = max(self.min_True - suppose_True, 0)
                max_Maybe = min(self.max_True - suppose_True, suppose_Maybe)
                self._combos[b] = choose_range(suppose_Maybe, min_Maybe, max_Maybe)
        return float(self._combos[tf]) / (self._combos[tf] + self._combos[not tf])


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
    state.n_deadends = 0
    
    def report_solution():
        state.n_solutions += 1
        if verbose:
            print "===== solution", state.n_solutions, len(state.log_stack), "====="
            sys.stdout.flush()
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
    return state.n_solutions, state.n_deadends


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
                    if verbose:
                        print "inferred", rc.row_col(i), False
                        sys.stdout.flush()
                    rc[i] = False
            rc.recount()
        if rc.n_Maybe() > 0 and rc.n_True() + rc.n_Maybe() == rc.min_True:
            for i in range(len(rc)):
                if rc[i] == Maybe:
                    if verbose:
                        print "inferred", rc.row_col(i), True
                        sys.stdout.flush()
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
            state.n_deadends += 1
            state.rewind()
            return

    if sum(row.n_Maybe() for row in state.rows) == 0:
        report_solution_fn()
        if multi:
            state.rewind()
            return
        else:
            raise Done()

    # Now all definite moves have been made above.  Pick the most "probable":

    maybeRows = [(i, row) for i, row in enumerate(state.rows) if row.n_Maybe() > 0]
    maybeCols = [(j, col) for j, col in enumerate(state.cols) if col.n_Maybe() > 0]
    f, i, j, tf = max((row.probability(tf) * col.probability(tf), i, j, tf)
                      for i, row in maybeRows for j, col in maybeCols
                      if state[i][j] == Maybe
                      for tf in [True, False])
    for tf in [tf, not tf]:
        if verbose:
            print "try", i, j, tf
            sys.stdout.flush()
        state.set(i, j, tf)
        spell_more(state, multi, report_solution_fn, verbose)
        if verbose:
            print "===== pop", len(state.log_stack), "====="
            sys.stdout.flush()
    state.rewind()
    return



if __name__ == "__main__":
    args = parse_args()
    dice = [Die(line) for line in open(args.dice)]
    n_solutions, n_deadends = spell(args.word, dice, args.many, args.count, args.verbose)
    if args.count:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
    print n_deadends, "dead ends"
    if n_solutions == 0:
        sys.exit(1)
