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


def spell(word):
    global dice, rows, cols
    
    dice = [Die(line) for line in open(args.dice)]
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
    spell_more(word, letters, letter_maxes, letter_mins, dice_maxes, dice_mins, state)


def print_solution(state, word, letters):
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


def move(state, log, row, col, new_value):
    log.append((row, col, state[row][col]))
    state[row][col] = new_value


def rewind(state, log):
    for row, col, value in reversed(log):
        state[row][col] = value


def count_rows_or_cols(state, log, p, q, maxes, mins):
    """
    p, q = 1, 0 to scan rows, or 0, 1 to scan columns.
    For any already-solved row/col with Maybes: turn them to false.
    For any unsolved row/col with *just enough* Maybes: turn them to True.
    Returns either  list of counts of Maybes, list of counts of Trues  for each row/col
                or  None, None if there is a row or column that can't be solved.
    """
    n_rows_or_cols = len(state) * p + len(state[0]) * q
    n_elements_each = len(state) * q + len(state[0]) * p
    maybes = [0] * n_rows_or_cols
    trues = [0] * n_rows_or_cols
    for i, r, c in ((i, i * p, i * q) for i in range(n_rows_or_cols)):
        for row, col in ((r + j * q, c + j * p) for j in range(n_elements_each)):
            trues[i] += (state[row][col] == True)
            maybes[i] += (state[row][col] == Maybe)
        assert trues[i] <= maxes[i]
        if trues[i] + maybes[i] < mins[i]:
            return None, None
        
        if trues[i] == maxes[i] and maybes[i] > 0:
            for row, col in ((r + j * q, c + j * p) for j in range(n_elements_each)):
                if state[row][col] == Maybe:
                    move(state, log, row, col, False)
            maybes[i] = 0
        if maybes[i] > 0 and trues[i] + maybes[i] == mins[i]:
            for row, col in ((r + j * q, c + j * p) for j in range(n_elements_each)):
                if state[row][col] == Maybe:
                    move(state, log, row, col, True)
            maybes[i] = 0
            trues[i] = mins[i]
    return maybes, trues


def spell_more(word, letters, letter_maxes, letter_mins, dice_maxes, dice_mins, state):
    log = []
    prev_len = -1
    while len(log) > prev_len:
        prev_len = len(log)
        dice_maybes, dice_trues = count_rows_or_cols(state, log, 1, 0, dice_maxes, dice_mins)
        if dice_maybes == None:
            rewind(state, log)
            return

        letter_maybes, letter_trues = count_rows_or_cols(state, log, 0, 1, letter_maxes, letter_mins)
        if letter_maybes == None:
            rewind(state, log)
            return

    if sum(dice_maybes) + sum(letter_maybes) == 0:
        print_solution(state, word, letters)
        rewind(state, log)
        return

    # Now all certain moves have been made above.  Pick the move with the least "freedom".

    def freedom(row, col):
        die_freedom = dice_maybes[row] + dice_trues[row] - dice_mins[row]
        letter_freedom = letter_maybes[col] + letter_trues[col] - letter_mins[col]
        return die_freedom * letter_freedom

    freedom, row, col = min((freedom(r, c), r, c) for r in rows for c in cols
                                                  if state[r][c] == Maybe)
    for tf in False, True:
        move(state, log, row, col, tf)
        spell_more(word, letters, letter_maxes, letter_mins, dice_maxes, dice_mins, state)
    rewind(state, log)


if __name__ == "__main__":
    args = parse_args()
    spell(args.word)
