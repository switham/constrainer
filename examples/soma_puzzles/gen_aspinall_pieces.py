#!/usr/bin/env python
""" gen_aspinall_pieces.py -- Math fun V 128 # 27. """

TEMPLATE = """\
X X X
. X .

. . X
. . .
-----
"""

LABELS = "123456789ABCDEFGHIJKLMNOP"


def gen_pieces(template, labels):
    for label in labels:
        print template.replace("X", label)


if __name__ == "__main__":
    gen_pieces(TEMPLATE, LABELS)




        
