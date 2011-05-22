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

Maybe = Maybies()


def spell(word, dice, multi=False, just_count=False):
    letters = list(set(word))
    rows = range(len(dice))
    cols = range(len(letters))
    letter_maxes = [sum(c == letter for c in word) for letter in letters]
    letter_mins = letter_maxes
    dice_maxes = [1] * len(dice)
    if len(dice) == len(word):
        dice_mins = dice_maxes
    else:
        dice_mins = [0] * len(dice)
    state = [[(letter in die.faces and Maybe) for letter in letters] for die in dice]

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


    def massage_rows_or_cols(move_fn, p, q):
        """
        (p, q) = (1, 0) to scan rows, or (0, 1) to scan columns.
        Scan rows or columns, drawing conclusions that are certain.
        If we're stuck, raise the Stuck exception.
        Returns two lists of counts: Maybes, and Trues, for each row/col.
        """
        n_rows_or_cols = len(dice) * p + len(letters) * q
        n_elements_each = len(dice) * q + len(letters) * p
        maxes = dice_maxes * p + letter_maxes * q
        mins = dice_mins * p + letter_mins * q
        maybes = [0] * n_rows_or_cols
        trues = [0] * n_rows_or_cols
        for i, r, c in ((i, i * p, i * q) for i in range(n_rows_or_cols)):
            for row, col in ((r + j * q, c + j * p) for j in range(n_elements_each)):
                trues[i] += (state[row][col] == True)
                maybes[i] += (state[row][col] == Maybe)
            if trues[i] + maybes[i] < mins[i] or trues[i] > maxes[i]:
                raise Stuck()

            if trues[i] == maxes[i] and maybes[i] > 0:
                for row, col in ((r + j * q, c + j * p) for j in range(n_elements_each)):
                    if state[row][col] == Maybe:
                        move_fn(row, col, False)
                maybes[i] = 0
            if maybes[i] > 0 and trues[i] + maybes[i] == mins[i]:
                for row, col in ((r + j * q, c + j * p) for j in range(n_elements_each)):
                    if state[row][col] == Maybe:
                        move_fn(row, col, True)
                maybes[i] = 0
                trues[i] = mins[i]
        return maybes, trues


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
            print >>sys.stdout, "No solutions."
        sys.exit(1)
