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


class StateRow(list):
    """ A list that saves state before changing an element.  See class State. """
    def __init__(self, log_stack, *args):
        super(StateRow, self).__init__(*args)
        self.log_stack = log_stack

    def __setitem__(self, j, newvalue):
        oldvalue = self[j]
        self.log_stack[-1].append(lambda: super(StateRow, self).__setitem__(j, oldvalue))
        super(StateRow, self).__setitem__(j, newvalue)


class State(list):
    """
    Classes State and StateRow together implement a two-dimensional array with undo.
    state.push()     # pushes a new empty stack frame for recording undo info.
    y = state[i][j]  # accessed like a regular 2D array.
    state[i][j] = x  # first magically records how to undo, into the current frame.
    state.pop()      # pops a stack frame and undoes its changes in reverse.
    """
    def __init__(self, *args):
        """ Initialize like you would a 2D array, i.e. with a sequence of sequences. """
        self.log_stack = []
        super(State, self).__init__(StateRow(self.log_stack, row) for row in list(*args))

    def depth(self): return len(self.log_stack)

    def push(self): self.log_stack.append([])

    def pop(self):
        for popper in reversed(self.log_stack.pop()):
            popper()
        return self.depth()
        

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


class StateView(object):
    """ A mutable 1D view into a 2D State, with True/False/Maybe constraints accounting. """
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
        self.state[i][j] = new_value
        self._combos[False] = self._combos[True] = NotCalculatedYet

    def __iter__(self): return (self[k] for k in range(len(self)))

    def recount(self):
        self._n_True = sum(value == True for value in self)
        self._n_Maybe = sum(value == Maybe for value in self)

    def n_True(self): return self._n_True

    def n_Maybe(self): return self._n_Maybe

    def set_Maybes(self, tf, verbose=False):
        for i in range(len(self)):
            if self[i] == Maybe:
                self[i] = tf
                if verbose:
                    print "inferred", self.row_col(i), tf
                    sys.stdout.flush()
                    
    def probability(self, tf):
        """
        Heuristic "probability" that a solution exists in which a random Maybe is set to tf.
        Actually, assume there is exactly ONE solution, and give odds that any given Maybe
        in this row or column is tf in the solution.
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


def spell(word, dice, multi=False, just_count=False, verbose=False):
    letters = list(set(word))
    state = State([(letter in die.faces and Maybe) for letter in letters] for die in dice)
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

        letter_dice = dict( (letter, [die for i, die in enumerate(dice) if state[i][j] == True])
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
        if rc.n_True() + rc.n_Maybe() < rc.min_True or rc.n_True() > rc.max_True:
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
    maybeRows = [(i, row) for i, row in enumerate(state.rows) if row.n_Maybe() > 0]
    maybeCols = [(j, col) for j, col in enumerate(state.cols) if col.n_Maybe() > 0]
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
            stuck, quiet = massage_rows_and_cols(state.rows + state.cols, verbose)
        if stuck:
            yield False

        elif sum(row.n_Maybe() for row in state.rows) == 0:
            yield True

        else:
            p, i, j, tf = most_probable_move(state)
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
    n_solutions, n_deadends = spell(args.word, dice, args.many, args.count, args.verbose)
    if args.count:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
    print n_deadends, "dead ends"
    if n_solutions == 0:
        sys.exit(1)
