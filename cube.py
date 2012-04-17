#!/usr/bin/env python
""" cube.py -- The Cube puzzle. """

from sys import stdout, stderr, exit
from maybies import *
from constrainer import *

from ddict import ddict
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzle", default="cube.dat",
        type=str, help="name of the file with the puzzle to solve")
    parser.add_argument("--pieces", metavar="file",
        type=str, default="cube_pieces.dat",
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


def canonical_shape_copy(shape):
    """ A shape is in canonical form when the mininums of x, y & z are zero. """
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
    show_rotations(["cube_pieces.dat", "cube.dat"])


def old_main():
    show_first_orientations("cube_pieces.dat", "cube.dat")
    show_first_rotations()


def solve(target, piece_shapes, multi=False, just_count=False, verbose=False):
    """
    target is a shape.
    piece_shapes is a dict of {label_letter: shape}.
    """
    # Quick summary:
    #     7 pieces, up to 27 target bloxels, up to about 700 piece-orientations.
    #     Let's only use "bloxel" to refer to points in the target.
    #     Two kinds of vars:
    #         orientation-is-used
    #         piece-is-unused
    #     Constraint types:
    #         Each bloxel is occupied exactly once.
    #         Each piece is in exactly one orientation, or unused.
    #         A certain number of pieces with four points are unused.
    #         Known ahead of time whether the 3-point "r" piece is used or not.
    # Comparison to spelling with letter-dice:
    #     A piece is like a die, an orientation is like a die face, and 
    #     a target bloxel is like a letter of the word to be spelled.
    #     But, each orientation occupies multiple bloxels, so a piece can
    #         potentially have alternative ways to occupy a bloxel.
    #         The useable die faces were vars at the intersection of one die
    #         and one letter.  But each cube piece orientation is a var
    #         constrained by one piece and by multiple bloxels.
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
    n_unused = {}
    n_4_pieces = sum(1 for piece in pieces if len(piece.shape) == 4)
    n_3_pieces = sum(1 for piece in pieces if len(piece.shape) == 3)
    assert n_3_pieces == 1 and n_3_pieces + n_4_pieces == len(pieces), \
        "Don't know how to work with this set of pieces, sorry!"
    n_unused[4] = n_4_pieces - (len(target) / 4)
    n_unused[3] = n_3_pieces - (len(target) % 4) / 3
    assert len(target) % 4 in (3, 0) and n_unused[4] >= 0, \
        "Target has %d bloxels, can't be made out of the pieces." % len(target)
    how_many_unused = {}
    for piece_size in 3, 4:
        how_many_unused[piece_size] = \
            BoolConstraint(state, piece_size=piece_size,
                                  min_True=n_unused[piece_size],
                                  max_True=n_unused[piece_size])

    # Now the variables:

    for piece in pieces:
        piece_unused = BoolVar(state, label="unused")
        oriented_one_way[piece].constrain(piece_unused)
        piece_size = len(piece.shape)
        how_many_unused[piece_size].constrain(piece_unused)
        
        piece.orientations = all_orientations_fitting(piece, target)
        for orientation in piece.orientations:
            bloxels = [point_bloxels[pt] for pt in orientation.shape]
            oriented_thus = BoolVar(state, orientation=orientation,
                                           bloxels=bloxels)
            oriented_one_way[piece].constrain(oriented_thus)
            for bloxel in bloxels:
                occupied_once[bloxel].constrain(oriented_thus)
            

    # Go solve it.
        
    n_solutions = 0
    n_deadends = 0
    for is_solution in state.generate_leaves(verbose):
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
        print "I'd like to show you the solution here."
        
        print
        if not multi:
            break
        
    return n_solutions, n_deadends


if __name__ == "__main__":
    args = parse_args()
    pieces = dict(read_labels_shapes(args.pieces))
    target_label, target = read_labels_shapes(args.puzzle) [0]
    
    n_solutions, n_deadends = solve(target, pieces,
                                    args.many, args.count, args.verbose)
    if args.count or args.many:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>stderr, "No solutions."
    print n_deadends, "dead ends"
    if n_solutions == 0:
        exit(1)

