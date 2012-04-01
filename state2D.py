#!/usr/bin/env python
"""
2D state array with 1D views and constraint bookkeeping.
"""

import sys
import argparse

from maybies import *

NotCalculatedYet = Maybies()


class StateRow(list):
    """
    A list that saves state before changing an element.  See class State2D.
    """
    def __init__(self, log_stack, arg):
        self.list = super(StateRow, self)
        self.list.__init__(arg)
        self.log_stack = log_stack

    def __setitem__(self, j, newvalue):
        oldvalue = self[j]
        self.log_stack[-1].append(lambda: self.list.__setitem__(j, oldvalue))
        self.list.__setitem__(j, newvalue)


class State2D(list):
    """
    Classes State2D and StateRow together implement a 2D array with undo.
    state.push()     # pushes a new empty stack frame for recording undo info.
    y = state[i][j]  # accessed like a regular 2D array.
    state[i][j] = x  # first records how to undo, into the current frame.
    state.pop()      # pops a stack frame and undoes its changes in reverse.
    """
    def __init__(self, arg):
        """ Initialize with a sequence of sequences. """
        self.list = super(State2D, self)
        self.log_stack = []
        self.list.__init__(StateRow(self.log_stack, row) for row in arg)

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
    """
    A mutable 1D view into a State2D,
    with True/False/Maybe constraints accounting.
    """
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
        Heuristic "probability" that a solution exists in which a random Maybe
        is set to tf.  Actually, assume there is exactly ONE solution, and
        give odds that any given Maybe in this row or column is tf in the
        solution.
        """
        if self._combos[tf] == NotCalculatedYet:
            # How many ways of filling in would be left
            # if one Maybe were set to True?  To False?
            assert self.n_Maybe() > 0
            m_Maybe = self.n_Maybe() - 1
            for b in True, False:
                suppose_True = self.n_True() + b
                min_Maybe = max(self.min_True - suppose_True, 0)
                max_Maybe = min(self.max_True - suppose_True, m_Maybe)
                self._combos[b] = choose_range(m_Maybe, min_Maybe, max_Maybe)
        ctf, cntf = self._combos[tf], self._combos[not tf]
        return float(ctf) / (ctf + cntf)


if __name__ == "__main__":
    print "No demo for this thing."
