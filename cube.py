#!/usr/bin/env python
""" cube.py -- The Cube puzzle. """


from constraints import *

# A shape is a list of 3D points as 3-tuples.
# Actually that's a shape in an "orientation".
# An "orientation" is a rotation plus a translation.


def read_shape(stream):
    shape = []
    heights = []
    widths = []
    chars = set()
    z = 0
    while True:
        y = 0  # y increases down the file and down the page.
        while True:
            line = stream.readline()
            if not line:
                assert shape == [], "Shape ends without dash (-)"

                return None

            line = line.strip()
            if line == "" or line[0] == '-':
                break

            # Regular lines are like "A A ."
            assert all(line[i] == " " for i in range(1, len(line), 2)), \
                "Alterating chars in shape lines must be blanks.  %r" % line

            width = len(line) / 2 + 1
            widths.append(width)
            for x in range(0, width):
                if line[x * 2] != '.':
                    shape.append( (x, y, z) )
                    chars.add(line[x * 2])
            y += 1
        if line != "":
            assert set(line) == set("-"), \
                "Dashed line must be all dashes.  " + repr(line)

            heights.append(y)
            break

        z += 1
    assert len(set(heights)) == 1, \
        "Heights of all layers of shape must match.  " + str(heights)

    assert len(set(widths)) == 1, \
        "Widths of all lines in a shape must match.  " + str(widths)

    assert len(chars) == 1, \
        "Should be only one significant character in a shape, not %s" % chars

    return list(chars)[0], shape


with open("cube_pieces.dat") as stream:
    while True:
        shape = read_shape(stream)
        if shape != None:
            print shape
        else:
            break

        

            
        
    
