#!/usr/bin/env python
""" cube.py -- The Cube puzzle. """

# from maybes import *
# from constrainer import *

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


def all_orientations_fitting(shape, target):
    """
    An "orientation" is a combination of a rotation and a translation
    of a specific puzzle piece.
    """
    return sum((all_translations_fitting(rs, target)
                for rs in all_unique_rotations(shape)), [])


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
        orientations = all_orientations_fitting(shape, target)
        print label, len(orientations), "orientations"
            

def show_first_rotations():
    show_rotations(["cube_pieces.dat", "cube.dat"])


def old_main():
    show_first_orientations("cube_pieces.dat", "cube.dat")
    show_first_rotations()


def solve(target, pieces, multi=False, just_count=False, verbose=False):
    """ target is a shape.  pieces is a dict of {label_letter: shape}. """
    # Quick summary:
    #     7 pieces, up to 27 target bloxels, up to about 700 piece-orientations.
    #     Let's only use "bloxel" to refer to points in the target.
    #     Two kinds of vars:
    #         orientation-is-used
    #         piece-unused  ("unused" is not an orientation as it has no var)
    #     Constraint types:
    #         Each bloxel is occupied exactly once.
    #         Exactly one orientation, or unused, per piece.
    #         A certain number of pieces with four points are unused.
    #         Known ahead of time whether the 3-point "r" piece is used or not.
    # Comparison to spelling with letter-dice:
    #     A piece is kinda like a die.
    #     An orientation is kinda like a face of a die.
    #     A target bloxel is kinda like a letter of the word to be spelled.
    #     But, each orientation occupies multiple bloxels, so a piece can
    #         potentially have alternative ways to occupy a bloxel.
    #         The useable die faces were vars at the intersection of one die
    #         and one letter.  But each orientation is a var constrained by
    #         one piece and by multiple bloxels.
    state = State(verbose=verbose)
    
    bloxels = list(set(target))
    for i, piece in enumerate(pieces):
        if not any(bloxel in piece.orientations for bloxel in bloxels):
            print "Piece", piece, "is not usable."
            pieces.pop(i)
    if len(pieces) < len(target):
        raise Exception("Not enough pieces to solve the puzzle!")

    # First we set up the Constrainers:

    bloxel_constraints = {}
    for bloxel in bloxels:
        # There are exactly as many pieces occupying a bloxel
        # as appearances of the bloxel in the target.
        n = sum(c == bloxel for c in target)
        bloxel_constraints[bloxel] = BoolConstraint(state, bloxel=bloxel,
                                                    min_True=n, max_True=n)

    # It helps here to treat unused pieces as like being
    # "used for nothing," or "occupying the null bloxel."
    # The number of unused pieces is exactly as many as the target doesn't need:
    n = len(pieces) - len(target)
    bloxel_constraints["unused"] = BoolConstraint(state, bloxel="unused",
                                                  min_True=n, max_True=n)

    # Each piece is used exactly once: to occupy a bloxel, or for nothing:
    piece_constraints = dict( (piece, BoolConstraint(state, piece=piece,
                                                     min_True=1, max_True=1))
                              for piece in pieces)

    # Now the Constrainees (variables):
    
    for bloxel in bloxels + ["unused"]:
        for piece in pieces:
            # Variables to say: this piece is used to occupy this bloxel
            # (or, this piece is not used).
            if bloxel == "unused" or bloxel in piece.orientations:
                piece_occupys_bloxel = BoolVar(state, piece=piece,
                                               bloxel=bloxel)
                bloxel_constraints[bloxel].constrain(piece_occupys_bloxel)
                piece_constraints[piece].constrain(piece_occupys_bloxel)
        
    n_solutions = 0
    n_deadends = 0
    for is_solution in state.generate_leaves(verbose):
        if not is_solution:
            n_deadends += 1
            continue

        n_solutions += 1
        if verbose:
            print "===== solution", n_solutions, state.depth(), "====="
            sys.stdout.flush()
        if just_count:
            continue

        # Show a solution.
        # For each bloxel, make a list of pieces that are occupying it.
        bloxel_pieces = dict( (bloxel, []) for bloxel in bloxels)
        for bloxel in bloxels:
            for var in bloxel_constraints[bloxel].vars:
                if var.value == Maybe:
                    print var.bloxel, var.piece, "Maybe??"
                    print var.bloxel, "constraints:"
                    print [c2.value for c2 in bloxel_constraints[var.bloxel].vars]
                    print var.piece, "constraints:"
                    print [c2.value for c2 in piece_constraints[var.piece].vars]
                if var.value:
                    bloxel_pieces[bloxel].append(var.piece)
        # Remove pieces from their lists as you use them to solve:
        for bloxel in target:
            piece = bloxel_pieces[bloxel].pop()
            print bloxel, piece
        print
        if not multi:
            break
        
    return n_solutions, n_deadends


if __name__ == "__main__":
    old_main()

elif False:
    args = parse_args()
    pieces = dict(read_labels_shapes(args.pieces))
    target_label, target = read_labels_shapes(args.puzzle)
    
    n_solutions, n_deadends = solve(target, pieces,
                                    args.many, args.count, args.verbose)
    if args.count or args.many:
        print n_solutions, "solutions."
    if n_solutions == 0:
        if not args.count:
            print >>sys.stderr, "No solutions."
    print n_deadends, "dead ends"
    if n_solutions == 0:
        sys.exit(1)

