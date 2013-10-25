#!/usr/bin/env python
""" soma.py -- Solver for Piet Hein's Soma cube puzzles. """

from sys import stdout, stderr, exit
from maybies import *
from constrainer import *
import os
import time

from ddict import ddict
import argparse

SHAPES_DIR = "soma_puzzles"
CUBE_FILE = os.path.join(SHAPES_DIR, "cube.dat")
PIECES_FILE = os.path.join(SHAPES_DIR, "soma_pieces.dat")

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzle", default=CUBE_FILE,
        type=str, help="name of the file with the puzzle to solve")
    parser.add_argument("--default_guess", default="False", metavar="BOOL",
        type=str, help="Always guess that a piece is/isn't in a place")
    parser.add_argument("--pieces", metavar="file",
        type=str, default=PIECES_FILE,
        help="name of file of descriptions of pieces ")
    parser.add_argument("--many", "--multi", "-m",
        action="store_true",
        help="generate as many solutions as possible, not just one")
    parser.add_argument("--count", "-c",
        action="store_true",
        help="just output a count of the number of solutions found")
    parser.add_argument("--verbose", "-v",
        action="store_true",
        help="show search progress")
    return parser.parse_args()


# A shape is a list of 3D points as 3-tuples.
# Actually that's a shape in an "orientation".
# An "orientation" is a rotation plus a translation of a piece.

class Piece(object):
    def __init__(self, label, shape):
        self.label = label
        self.shape = shape

    def __str__(self):
        return self.label

    def __repr__(self):
        return "Piece(%r,...)" % self.label


class Bloxel(object):
    """ a point within the target shape """
    def __init__(self, point):
        self.point = point

    @staticmethod
    def name(point):
        return "%1X%1X%1X" % point

    def __str__(self):
        return Bloxel.name(self.point)

    def __repr__(self):
        return "Bloxel(%r)" % Bloxel.name(self.point)


class Orientation(object):
    def __init__(self, piece, shape):
        self.piece = piece
        self.shape = shape

    def __str__(self):
        return '_'.join(Bloxel.name(pt) for pt in self.shape)

    def __repr__(self):
        return "Orientation(%s, %s)" % (self.piece, str(self))
        

def print_points_labels(point_labels):
    shape = point_labels.keys()
    maxes = [max(pt[dim] for pt in shape) for dim in range(3)]
    # Layers of the picture back to front (decreasing z):
    for z in range(maxes[2], -1, -1):
        # y increases going down:
        for y in range(maxes[1] + 1):
            print " ".join(point_labels.get((x, y, z), '.')
                           for x in range(maxes[0] + 1))
        if z > 0:
            print
    print "-" * (maxes[0] * 2 + 1)


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

                return None, None

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

    return list(chars)[0], canonical_shape_copy(shape)


def read_labels_shapes(filename):
    """
    Read shapes, each with a letter label, and return a list of
    (letter, shape).
    """
    results = []
    with open(filename) as stream:
        while True:
            label, shape = read_label_shape(stream)
            if not shape:
                break

            results.append( (label, shape) )
    return results


def canonical_shape_copy(shape):
    """ A shape is in canonical form when the mininums of x, y & z are zero. """
    mins = [min(pt[dim] for pt in shape) for dim in range(3)]
    new = [tuple(pt[dim] - mins[dim] for dim in range(3)) for pt in shape]
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


def translate_shape(shape, dx, dy, dz):
    return tuple((x + dx, y + dy, z + dz) for x, y, z in shape)


def all_translations_fitting(shape, target):
    t_sizes = tuple(max(pt[dim] for pt in target) + 1 for dim in range(3))
    s_sizes = tuple(max(pt[dim] for pt in shape) + 1 for dim in range(3))
    target_set = set(target)
    survivors = []
    for dx in range(t_sizes[0] - s_sizes[0] + 1):
        for dy in range(t_sizes[1] - s_sizes[1] + 1):
            for dz in range(t_sizes[2] - s_sizes[2] + 1):
                candidate = translate_shape(shape, dx, dy, dz)
                if all(pt in target_set for pt in candidate):
                    survivors.append(candidate)
    return survivors


def all_orientations_fitting(piece, target):
    """
    An "orientation" is a combination of a rotation and a translation
    of a specific puzzle piece.
    """
    shapes = sum((all_translations_fitting(rs, target)
                for rs in all_unique_rotations(piece.shape)), [])
    return [Orientation(piece, shape) for shape in shapes]


def range_cover(values, step=1):
    if step > 0:
        return range(min(values), max(values) + 1)
    else:
        return range(max(values), min(values) - 1, -1)


def shape_to_pic(shape):
    other_pic = [ "       +          ",
                  "     /   \        ",
                  "   /       \      ",
                  " +           +    ",
                  " | \       / |    ",
                  " |   \   /   |    ",
                  " +     +     +    ",
                  "   \   |   /      ",
                  "     \ | /        ",
                  "       +          ", ]
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
    

def print_array_of_pics(pics, n_up=2):
    for i in range(0, len(pics), n_up):
        stop = min(i + n_up, len(pics))
        print '\n'.join(pics_side_by_side(pics[i : stop]))
        print
    

def show_rotations(filenames):
    for filename in filenames:
        for label, shape in read_labels_shapes(filename):
            print label + ":", shape
            rotations = all_unique_rotations(shape)
            print len(rotations), "rotations:"
            print
            print_array_of_pics([shape_to_pic(s) for s in rotations])


def show_first_orientations(shapes_filename, target_filename):
    target_label, target = read_labels_shapes(target_filename) [0]
    for label, shape in read_labels_shapes(shapes_filename):
        orientations = all_orientations_fitting(Piece(label, shape), target)
        print label, len(orientations), "orientations"
            

def show_first_rotations():
    show_rotations([PIECES_FILE, CUBE_FILE])


def old_main():
    show_first_orientations(PIECES_FILE, CUBE_FILE)
    show_first_rotations()


def solve(target, piece_shapes, multi=False, just_count=False,
          verbose=False, default_guess=None):
    """
    target is a shape.
    piece_shapes is a dict of {label_letter: shape}.
    """
    # 7 pieces, up to 27 target bloxels, up to about 700 piece-orientations.
    # Let's only use "bloxel" to refer to points in the target.
    state = State(verbose=verbose)

    # First we set up the Constraints:

    # Each bloxel is occupied exactly once.
    point_bloxels = dict( (point, Bloxel(point)) for point in target)
    bloxels = point_bloxels.values()
    occupied_once = {}
    for bloxel in bloxels:
        occupied_once[bloxel] = BoolConstraint(state, bloxel=bloxel,
                                                      min_True=1, max_True=1)

    # Each piece is used exactly once: to occupy a bloxel, or for nothing:
    labeled_pieces = dict( (label, Piece(label, shape))
                           for label, shape in piece_shapes.iteritems())
    pieces = labeled_pieces.values()
    oriented_one_way = {}
    for piece in pieces:
        oriented_one_way[piece] = BoolConstraint(state, piece=piece,
                                                        min_True=1, max_True=1)

    # Constraints on how many pieces are unused, for two sizes of piece:
    n_4_pieces = sum(1 for piece in pieces if len(piece.shape) == 4)
    n_3_pieces = sum(1 for piece in pieces if len(piece.shape) == 3)
    assert n_3_pieces == 1 and n_3_pieces + n_4_pieces == len(pieces), \
        "Don't know how to work with this set of pieces, sorry!"
    n_unused = {4: n_4_pieces - (len(target) / 4),
                3: n_3_pieces - (len(target) % 4) / 3}
    assert len(target) % 4 in (3, 0) and n_unused[4] >= 0, \
        "Target has %d bloxels, can't be made out of the pieces." % len(target)
    how_many_unused = {}
    for piece_size in 3, 4:
        how_many_unused[piece_size] = \
            BoolConstraint(state, piece_size=piece_size,
                                  min_True=n_unused[piece_size],
                                  max_True=n_unused[piece_size])
    t_unused = sum(n_unused.values())
    if t_unused == 0:
        print "All", len(pieces), "pieces used."
    else:
        print len(pieces) - t_unused, "pieces used."
    # Now the variables:

    for piece in pieces:
        piece_unused = BoolVar(state, piece=piece, label="unused")
        oriented_one_way[piece].constrain(piece_unused)
        piece_size = len(piece.shape)
        how_many_unused[piece_size].constrain(piece_unused)
        
        for orientation in all_orientations_fitting(piece, target):
            orient_bloxels = [point_bloxels[pt] for pt in orientation.shape]
            piece_oriented_thus = BoolVar(state, orientation=orientation,
                                                 bloxels=orient_bloxels)
            oriented_one_way[piece].constrain(piece_oriented_thus)
            for bloxel in orient_bloxels:
                occupied_once[bloxel].constrain(piece_oriented_thus)

    # Go solve it.
        
    n_solutions = 0
    n_deadends = 0
    for is_solution in state.generate_leaves(verbose,
                                             default_guess=default_guess):
        if not is_solution:
            n_deadends += 1
            continue

        n_solutions += 1
        if not just_count or verbose:
            print "==== solution", n_solutions, "depth", "%d," % state.depth(),
            print n_deadends, "dead ends ===="
            stdout.flush()
        if just_count:
            continue

        # Show a solution.
        point_labels = {}
        for bloxel in bloxels:
            occupiers = occupied_once[bloxel][True]
            assert len(occupiers) == 1
            orientation_var = list(occupiers) [0]
            piece = orientation_var.orientation.piece
            point_labels[bloxel.point] = piece.label
        print_points_labels(point_labels)
        
        print
        if not multi:
            break
        
    return n_solutions, n_deadends


if __name__ == "__main__":
    args = parse_args()
    pieces = dict(read_labels_shapes(args.pieces))
    target_label, target = read_labels_shapes(args.puzzle) [0]
    default_guess = (args.default_guess == "True")
    print "default_guess =", default_guess
    start = time.clock()
    n_solutions, n_deadends = solve(target, pieces,
                                    args.many, args.count, args.verbose,
                                    default_guess=default_guess)
    if args.count or args.many:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>stderr, "No solutions."
    print n_deadends, "dead ends", time.clock() - start, "sec."
    if n_solutions == 0:
        exit(1)

