import random
import bisect
import math

# adapted from Peter Otten
#  http://mail.python.org/pipermail/python-list/2005-October/344557.html
def cumsum(items, sigma=0.0):
    """
    Yield iterable of same length as first arg, with cumulative sums
    of given items.
    Initial sum "sigma" defaults to 0.0.
    """

    for item in items:
        sigma += item
        yield sigma

def weightedsample(seq, weights, n=1, replace=False, prng=random.random):
    """Select n items from seq, weighted by the corresponding entries in weights,
    with or without replacement.
    By default, use the python random.random() function, but an alternate can be provided.  E.g.
    >>> erandom.weightedsample(['a','b','c'], [1,2,3], 3, True, itertools.cycle([.9,.9,.8]).next)
    """

    result = []
    cum_weights = list(cumsum(weights))
    tot = cum_weights[-1]

    for _ in xrange(n):
        i = bisect.bisect(cum_weights, prng() * tot)
        result.append(seq[i])
        if not replace:
            del seq[i:i+1]
            del weights[i:i+1]
            cum_weights = list(cumsum(weights))
            tot = cum_weights[-1]

    return result

def ssr(precinct, seed):
    """
    Sum of Square Roots (SSR) pseudorandom function from Rivest, 2008:
    http://people.csail.mit.edu/rivest/Rivest-ASumOfSquareRootsSSRPseudorandomSamplingMethodForElectionAudits.pdf

    Input: precinct number (as an integer) and seed (a string of 15 digits)

    >>> ssr(23951, "279016755606125")
    0.93591273640868167

                        0.93591273640868167
    vs from paper: xi = 0.93591273640858040364659219
    """

    if not seed  or  len(seed) < 15:
        return ""

    p = "%06d" % precinct
    return math.modf(math.sqrt(int(p[0:2] + seed[ 0: 5])) +
                     math.sqrt(int(p[2:4] + seed[ 5:10])) +
                     math.sqrt(int(p[4:6] + seed[10:15])) )[0]
