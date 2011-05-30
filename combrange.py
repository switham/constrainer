#!/usr/bin/env python
""" sum of combinations over a range """

def choose( n, k ):
    """ Combinations of k things out of n """
    if k > n:
        return 0;

    if k > n / 2:
        k = n - k  # Take advantage of symmetry.

    accum = 1
    for i in range( 1, k+1 ):
        accum = accum * ( n - k + i ) / i

    return accum


def choose_range_obvious(n, j, k):
    return sum(choose(n, i) for i in range(j, k + 1))


def choose_range_simple(n, j, k):
    """
    How many subsets of between j and k out of n things are there?
    Like sum(choose(n, i) for i in range(j, k + 1)) but linear with n.
    """
    if k < j:  return 0
    assert 0 <= j and k <= n
    term = 1
    t = 0
    for i in range(k):
        if i >= j:  t += term
        term = term * (n - i) / (i + 1)
    return t + term


def choose_range(n, j, k):
    """
    How many subsets of between j and k out of n things are there?
    Like sum(choose(n, i) for i in range(j, k + 1)) but linear with n.
    This is about a fast as choose_range_simple when n = 8,
    1.5 x when n = 50, 2x when n = 1024.  For "the average case."
    """
    if k < j:  return 0
    assert 0 <= j and k <= n

    if j > n / 2:
        j, k = n - k, n - j
    if k < n / 2:
        term = 1
        t = 0
        for i in range(k):
            if i >= j:  t += term
            term = term * (n - i) / (i + 1)
        return t + term

    else:
        k = n - k
        term = 1
        t = 0
        for i in range(max(j, k)):
            if i < j: t -= term
            if i < k: t -= term
            term = term * (n - i) / (i + 1)
        return 2**n + t
            

def choose_range_test(n, j, k):
    x = choose_range_obvious(n, j, k)
    y = choose_range(n, j, k)
    assert x == y, (n, j, k, x, y)
    return x


def timing_test(n, f, reps):
    cases = []
    for repeat in range(reps):
        j = randrange(n + 1)
        k = randrange(n)
        if j > k:
            j, k = k, j - 1
        cases.append((j, k))
    start = time.time()
    for j, k in cases:
        f(n, j, k),
    return (time.time() - start) / reps



# More optimizations:
# 1) If j and k are both on the high side of n/2, flip to the low side.
# 2) If j and k straddle the midpoint,
#    flip k, then do 2**n minus the missing values:
#    t = 0
#    for i in range(max(j, flipped_k)):
#       term = choose(i, n)  # but computed incrementally
#       if i < j: t -= term
#       if i < flipped_k: t -= term
#    return 2**n + t
#
# Both tricks should reduce the number of calculations but also the
# sizes of the intermediate results although that's pretty flat
# once i reaches n/2.


if __name__ == "__main__":
    import time, math
    from random import randrange
    
    for n in range(0, 9):
        for k in range(n + 1):
            print (choose(n, k), choose_range_test(n, 0, k)),
        print
    print

    n = 13
    for j in range(n + 1):
        for k in range(j, n + 1):
            print choose_range_test(n, j, k),
        print
    print

    fs = [choose_range_obvious, choose_range_simple, choose_range]
    reps = dict((f, 1000) for f in fs)
    print "n",
    for f in fs:
        print f.__name__,
    print
    for n in [c * 2 ** p for p in range(2, 11) for c in [2, 3]]:
        print n,
        for f in fs:
            t = timing_test(n, f, reps[f])
            reps[f] = int(math.ceil(2.0 / t))
            print t,
        print
