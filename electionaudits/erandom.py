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

def weightedsample(seq, weights, n=1):
    "select n items from seq, weighted by weights, without replacement"

    result = []
    for _ in xrange(n):
        cum_weights = list(cumsum(weights))
        tot = cum_weights[-1]

        i = bisect.bisect(cum_weights, random.uniform(0, tot))
        result.append(seq[i])
        del seq[i:i+1]
        del weights[i:i+1]
        
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

    p = "%06d" % precinct
    return math.modf(math.sqrt(int(p[0:2] + seed[ 0: 5])) +
                     math.sqrt(int(p[2:4] + seed[ 5:10])) +
                     math.sqrt(int(p[4:6] + seed[10:15])) )[0]
