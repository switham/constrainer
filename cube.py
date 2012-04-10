#!/usr/bin/env python
""" cube.py -- The Cube puzzle. """

# from maybes import *
# from constrainer import *

from ddict import ddict

# A shape is a list of 3D points as 3-tuples.
# Actually that's a shape in an "orientation".
# An "orientation" is a rotation plus a translation.


def read_label_shape(stream):
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


def canonical_shape_copy(shape):
    mins = tuple(min(pt[dim] for pt in shape) for dim in range(3))
    new = (tuple(pt[dim] - mins[dim] for dim in range(3)) for pt in shape)
    return tuple(sorted(new))


def rotate_shape_copy(shape, dim1, dim2):
    new_shape = []
    for pt in shape:
        new_pt = list(pt)
        new_pt[dim1] = -pt[dim2]
        new_pt[dim2] = pt[dim1]
        new_shape.append(new_pt)
    return canonical_shape_copy(new_shape)


def all_unique_rotations(shape):
    rotations = set()
    shape1 = canonical_shape_copy(shape)
    for i in range(4):
        shape1 = rotate_shape_copy(shape1, 0, 1)
        shape2 = canonical_shape_copy(shape1)
        for j in range(4):
            shape2 = rotate_shape_copy(shape2, 1, 2)
            shape3 = canonical_shape_copy(shape2)
            for k in range(4):
                shape3 = rotate_shape_copy(shape3, 0, 2)
                rotations.add(shape3)
    return list(rotations)


def range_cover(values, step=1):
    if step > 0:
        return range(min(values), max(values) + 1)
    else:
        return range(max(values), min(values) - 1, -1)


def shape_to_pic(shape):
    cube_pic = [ "##+---------+",
                 "#/         /|",
                 "+---------+ |",
                 "|         | |",
                 "|         | +",
                 "|         |/#",
                 "+---------+##", ]
    xyz_to_pic_col_row = [(10, 0), (0, 4), (2, -2)]
    # For each point seen in the resulting pic,
    # keep a list of (-z, x, y, -char):
    zbuf = ddict[ddict[list]] ()
    for (x, y, z) in shape:
        pic_col, pic_row = (0, 0)
        for val, (colf, rowf) in zip((x, y, z), xyz_to_pic_col_row):
            pic_col += val * colf
            pic_row += val * rowf
        for row, line in enumerate(cube_pic):
            for col, c in enumerate(line):
                if c != '#':
                    zbuf[row + pic_row][col + pic_col].append( (-z, x, -y, c) )
    pic = []
    for row in range_cover(zbuf.keys()):
        row_str = ""
        if row in zbuf:
            row_buf = zbuf[row]
            for col in range(max(row_buf.keys()) + 1):
                if col in row_buf:
                    minus_z, x, minus_y, c = max(row_buf[col])
                    row_str += c
                else:
                    row_str += ' '
        pic.append(row_str)
    return pic


def ljust_pic(pic):
    width = max(len(line) for line in pic)
    return [line.ljust(width) for line in pic], width


def pics_side_by_side(pics):
    widths = [None] * len(pics)
    for i in range(len(pics)):
        pics[i], widths[i] = ljust_pic(pics[i])
    height = max(len(pic) for pic in pics)
    for i in range(len(pics)):
        pics[i] += (height - len(pics[i])) * [" " * widths[i]]
    for i in range(height):
        yield "     ".join(pic[i] for pic in pics)
    

def print_array_of_pics(pics, n_up=12):
    for i in range(0, len(pics), n_up):
        stop = min(i + n_up, len(pics))
        print '\n'.join(pics_side_by_side(pics[i : stop]))
        print
    

for filename in "cube_pieces.dat", "cube.dat":
    with open(filename) as stream:
        while True:
            descr = read_label_shape(stream)
            if descr != None:
                label, shape = descr
                print label + ":", shape
                rotations = all_unique_rotations(shape)
                print len(rotations), "rotations:"
                print
                print_array_of_pics([shape_to_pic(s) for s in rotations])
            else:
                break
            
