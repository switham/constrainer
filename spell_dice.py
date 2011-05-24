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
    def __init__(self):
        self.log_stack = []
        self.listeners = [[list() for col in self[0]] for row in self]

    def _inform_listeners_and_set(self, row, col, new_y):
        old_y = self[row][col]
        for listener in self.listeners[row][col]:
            listener(old_y, new_y)
        self[row][col] = new_y

    def set(self, row, col, new_y):
        self._inform_listeners_and_set(row, col, new_y)
        self.log_stack[-1].append(row, col, old_y)

    def rewind(self):
        for row, col, popped_y in reversed(pop(self.log_stack)):
            self._inform_listeners_and_set(row, col, popped_y)
        

class StateRowOrCol(object):
    def __init__(self, state, r0, c0, dr, dc, min_True, max_True):
        self.state = state
        self.r0, self.c0 = r0, c0
        self.dr, self.dc = dr, dc
        self.min_True, self.max_True = min_True, max_True
        #
        self.len = len(state) * dr + len(state[0]) * dc
        self._n_True = sum(x == True for x in self)
        self._n_Maybe = sum(x == Maybe for x in self)
        for i in range(len(self)):
            r, c = self.row_col(i)
            self.state.listeners[row][col].append(self._hear)

    def __len__(self):
        return self.len

    def n_True(self): return self._n_True

    def n_Maybe(self): return self._n_Maybe

    def row_col(self, i):
        return self.r0 + i * self.dr, self.c0 + i * self.dc
    
    def __getitem__(self, x):
        r, c = self.row_col(x)
        return self.state[r][c]
        
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __setitem__(self, x, new_y):
        r, c = self.row_col(x)
        self.state.set(r, c, new_y)

    def _hear(self, old_y, new_y):
        self.n_True += -(old_y == True) + (new_y == True)
        self.n_Maybe += -(old_y == Maybe) + (new_y == Maybe)


def spell(word, dice, multi=False, just_count=False):
    letters = list(set(word))
    state = [[(letter in die.faces and Maybe) for letter in letters] for die in dice]
    log_stack = []
    letter_cols = []
    for j, letter in enumerate(letters):
        min_True = max_True = [sum(c == letter for c in word)]
        letter_cols.append(StateRowOrCol(state, log_stack, 0, j, 0, 1, min_True, max_True))
    dice_rows = []
    if len(dice) == len(word):
        min_True, max_True = 1, 1
    else:
        min_True, max_True = 0, 1
    for i, die in enumerate(dice):
        dice_rows.append(StateRowOrCol(state, log_stack, i, 0, 1, 0, min_True, max_True))
    spell.n_solutions = 0
    
    class Done(Exception):
        pass

    class Stuck(Exception):
        pass

    def solution():
        spell.n_solutions += 1
        if just_count:
            return
        
        letter_dice = collections.defaultdict(list)
        for col in cols:
            letter = letters[col]
            for row in rows:
                if state[row][col] == True:
                    letter_dice[letter].append(dice[row])
        for letter in word:
            die = letter_dice[letter].pop()
            print letter, die
        print


    def massage_rows_or_cols(rcs):
        """
        Scan rows or columns, drawing conclusions that are certain.
        If we're stuck, raise the Stuck exception.
        """
        for rc in rcs:
            if rc.n_True() + rc.n_Maybe() < rc.min_True or rc.n_True() > rc.max_True:
                raise Stuck()

            if rc.n_True() == rc.max_True and rc.n_Maybe() > 0:
                for i in range(len(rc)):
                    if rc[i] == Maybe:
                        rc[i] = False
            if rc.n_Maybe() > 0 and rc.n_True() + rc.n_Maybe() == rc.min_True:
                for i in range(len(rc)):
                    if rc[i] == Maybe:
                        rc[i] = True


    def spell_more():
        log = []

        def move(row, col, new_value):
            log.append((row, col, state[row][col]))
            state[row][col] = new_value

        def rewind():
            for row, col, value in reversed(log):
                state[row][col] = value

        prev_len = -1
        while len(log) > prev_len:
            prev_len = len(log)
            try:
                dice_maybes, dice_trues = massage_rows_or_cols(move, 1, 0)
                letter_maybes, letter_trues = massage_rows_or_cols(move, 0, 1)
            except Stuck:
                rewind()
                return

        if sum(dice_maybes) + sum(letter_maybes) == 0:
            solution()
            if multi:
                rewind()
                return
            else:
                raise Done()

        # Now all certain moves have been made above.  Pick the move with the least "freedom".

        def freedom(row, col):
            die_freedom = dice_maybes[row] + dice_trues[row] - dice_mins[row]
            letter_freedom = letter_maybes[col] + letter_trues[col] - letter_mins[col]
            return die_freedom * letter_freedom

        f, row, col = min((freedom(r, c), r, c) for r in rows for c in cols
                                                      if state[r][c] == Maybe)
        for tf in False, True:
            move(row, col, tf)
            spell_more()
        rewind()
        return

    try:
        spell_more()
    except Done:
        pass
    return spell.n_solutions


if __name__ == "__main__":
    args = parse_args()
    dice = [Die(line) for line in open(args.dice)]
    n_solutions = spell(args.word, dice, args.many, args.count)
    if args.count:
        print n_solutions
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
        sys.exit(1)
