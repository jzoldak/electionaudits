# varsize.py
# Author: Ronald L. Rivest
# Released under the MIT (aka X11) license
# Revised for use in ElectionAudits by Neal McBurnett
# Based on version from Rivest: "Last modified: 2007-11-17"
#  dated 2008-01-17 from http://people.csail.mit.edu/rivest/pps/varsize.py

"""
varsize.py: Routines to work with various election audit sample size strategies

Reference: 
 On Auditing Elections When Precincts Have Different Sizes
 by Javed A. Aslam, Raluca A. Popa and Ronald L. Rivest, 2007-01-17.
 http://people.csail.mit.edu/rivest/AslamPopaRivest-OnAuditingElectionsWhenPrecinctsHaveDifferentSizes.pdf
"""

import math
import random
import sys

# A precinct is represented as a pair (size, name)

#####################################################################
#####################################################################
### INPUT
#####################################################################
#####################################################################

def read_precincts(source):
    """
    Read input from the source and return the list of precinct (size,name)
    pairs sorted by decreasing size.
    source can be the name of a csv (comma-separated values) file where
    each line has as its first two components: size and (optional) name,
    or a python list of (size, name) pairs.
    """

    if hasattr(source,'__iter__'):
        return sort_by_size(source)

    else:
        lines = open(source).readlines()
        L = make_precinct_list(lines)
        return L

def sort_by_size(L):
    """
    Return a copy of precinct list L, sorted into decreasing order by size.
    """
    answer = L[:]                  
    answer.sort()
    answer.reverse()
    return answer

def make_precinct_list(lines):
    """
    Return list of precincts from a list of lines.
    
    Input has One line per precinct; blank lines ignored.
    Each input line has the format:
        size,name,
    (Everything between first two commas is the precinct name.)
    Example three-line input:
        424, Middlesex 1,
        324, Middlesex 2,
        1300, North Cambridge 11,
    If the precinct name is omitted, it defaults to:
        "P_1" for the precinct of the first line, 
        "P_2" for the next precinct, etc.
    """
    L = []
    # Create one precinct pair per line
    for i,line in enumerate(lines):
        line = line.strip()
        parts = line.split(",",1)
        if len(parts)==0: continue       # blank line
        precinct_size = int(parts[0])
        if len(parts)>1:                 # name given
            precinct_name = parts[1]  
        else:                            # no name given
            precinct_name = "P_%d"%(i+1) # use e.g. P_45
        precinct = (precinct_size,precinct_name)
        L.append(precinct)
    return sort_by_size(L)

def print_precinct_stats(L):
    """
    Print simple statistics about the precincts in L.
    """
    print
    if __name__ == "__main__":
        print "Precinct list (sorted into decreasing order by size):"
        for prc in L:
            print "  Precinct %s: size %d"%(prc[1],prc[0])
    n = len(L)
    print "Number of precincts:",n
    V = sum([x[0] for x in L])  
    print "Total number of votes cast: ",V
    Vave = float(V)/n
    print "Average number of votes/precinct:",Vave
    Vmed = L[n/2][0]
    print "Median number of votes/precinct:",Vmed
    Vmax = max([x[0] for x in L])
    print "Maximum number of votes/precinct:",Vmax
    Vmin = min([x[0] for x in L])
    print "Minimum number of votes/precinct:",Vmin
    print "Ratio of max/min:",float(Vmax)/Vmin

#####################################################################
#####################################################################
#####################################################################
### EQUAL-SIZED PRECINCTS
#####################################################################
#####################################################################
#####################################################################

def rule_of_thumb(m,alpha=0.92,s=0.20):
    """
    Return number of precincts to audit for given margin m.
        m = margin of victory a fraction of total votes cast
    Roughly 92\% confidence rate.
    """
    return 1.0/m * (- 2.0 * s * math.ln(alpha))

def APR(n,m,alpha=0.08,s=0.20):
    """
    Return number of (equal-sized) precincts to audit.
    Use Aslam/Popa/Rivest (nearly exact) approximation formula
       n = number of precincts
       m = margin of victory as a fraction of total votes cast
       alpha = significance level desired = 1 - confidence
       s = maximum within-precinct-miscount
    """
    if m == 0.0:
        return n
    b = math.ceil(n * (m / (2 * s)))
    u = (n - (b-1)/2.0)*(1.0-math.pow(alpha,1.0/b))
    return u

def sample_uniformly(L,u):
    """
    Return a random sample of size u of the given list of precincts.

    Select a subset of size u uniformly at random.
    Return them sorted into decreasing order.
    Uses 'random' module -- do not use for real elections!
    """
    S = random.Random().sample(L,u)
    return sort_by_size(S)

def confidence_for_uniform_audit(n,u,b):
    """
    Return the chance of seeing one of b bad precincts in a
    uniformly drawn sample of size u, from a set of size n.
    """
    miss_prob = 1.0
    for i in range(int(u)):
        miss_prob *= float(n-b-i)/(n-i)
    return 1.0 - miss_prob

#####################################################################
#####################################################################
#####################################################################
### VARIABLE-SIZED PRECINCTS
#####################################################################
#####################################################################
#####################################################################

#####################################################################
### SAFE method
#####################################################################

def bmin(L,M,s=0.20):
    """
    Return minimum number of precincts that could be "bad".
       L = list of n precincts: n (size,name) pairs
       M = margin of victory as number of votes separating winner 
           from runner-up
       s = maximum within-precinct miscount
    """
    assert 0 <= M <= sum(x[0] for x in L)
    votes_so_far = 0
    k = 0          # precincts taken
    while votes_so_far < M  and  k < len(L):
        votes_so_far += 2.0*s*L[k][0]
        k += 1
    return k

def safe_u(L,M,alpha=0.08,s=0.20):
    """
    Return number u of precincts to audit in "SAFE" method.
        L = list of n precincts: n (size, name) pairs
        M = margin of victory as number of votes separating winner
            from runner-up
        alpha = significance level desired = 1 - confidence
        s = maximum within-precinct miscount
    """
    b = bmin(L,M)
    V = float(sum([x[0] for x in L]))
    u = (n - (b-1)/2.0)*(1.0-math.pow(alpha,1.0/b))
    return u

#####################################################################
#####################################################################
### BASIC auditing: precincts selected independently but nonuniformly
#####################################################################
#####################################################################

def sample_independently(L,p):
    """
    Return a sample of the given list of precincts, sampled according to p.
        L = input list of precincts, 0<=i<n; each is (size,name) pair.
        p = input list of their probabilities.
    Select precincts with probability proportional to probabilities in p.
    Each precinct is selected *independently*.
    """
    n = len(L)
    sample = []
    for i in range(n):
        if random.random() <= p[i]:
            sample.append(L[i])
    return sample

def expected_number_of_precincts_audited(p):
    """
    Return expected number of precincts audited.
       p = list of probabilities that each precinct will be audited
    """
    return sum(p)

def expected_workload(L,p):
    """
    Return expected number of votes that need to be counted.
        L = input list of precincts: (size,name) pairs.
        p = input list of auditing probabilities.
    """
    return sum([p[i]*L[i][0] for i in range(len(L))])

#####################################################################
### Negative-exponential auditing method
#####################################################################

def negexp_probs_for_number_of_precincts(L,u):
    """
    Return vector of probabilities for the precincts, and w,
    so that they follow the negexp approach, but so that
    the expected number of precincts sampled is
    exactly u.  

    Assumes input list L of precincts is sorted by decreasing size.
    """

    import scipy.optimize

    def f(w):
        """
        Auxiliary function: return expected number of precinct audited, minus k.
        """
        return sum([1.0-math.exp(-L[i][0]/w) for i in range(len(L))])-u
    # Find w that makes f(w)==0, min_w <= w <= max_w
    min_w = 0.001
    max_w = L[0][0]*100.0
    w = scipy.optimize.brentq(f,min_w,max_w)
    return [1.0-math.exp(-L[i][0]/w) for i in range(len(L))],w

def negexp_probs_for_workload(L,A):
    """
    Return vector of probabilities for the precincts, and w, 
    so that they follow the negexp approach, but so that
    the expected workload (number of votes audited) is
    exactly A.  Assumes L is sorted by decreasing size.
    """

    import scipy.optimize

    def f(w):
        """
        Auxiliary function returns expected number of votes to be audited, minus A.
        """
        return sum([(1.0-math.exp(-L[i][0]/w))*L[i][0] for i in range(len(L))])-A
    # Find w that makes f(w)==0, min_w <= w <= max_w
    min_w = 0.001
    max_w = L[0][0]*100.0
    w = scipy.optimize.brentq(f,min_w,max_w)
    return [1.0-math.exp(-L[i][0]/w) for i in range(len(L))],w

def negexp_probs_for_confidence(L,M,alpha,s=0.20):
    """
    Return p,w , where p = vector of probabilities for the precincts, 
    so that they follow the negexp approach, but so that
    the expected confidence in detecting fraud of at least
    C votes is at least 1-alpha
    Assumes that L is sorted into decreasing order.
    """
    w = -M/math.log(alpha)
    if w != 0.0:
        return [(1.0-math.exp(-L[i][0]*2.0*s/w)) for i in range(len(L))],w
    else:
        return [(1.0) for i in range(len(L))],w

def negexp_strategy(L,k):
    """
    Return a strategy for picking a sample of size k from
    the given list of precincts.

    Assumes precincts listed in decreasing order by size.
    """
    p,w = negexp_probs_for_number_of_precincts(L,k)
    strategy = make_strategy_from_probs(L,p,k)
    return strategy

#####################################################################
### ppebwr auditing method
#####################################################################

def ppebwr_round_probs(L):
    """
    Return 'round probabilities' for use in ppebwr method.
    These are just scaled precinct sizes.
    """
    V = float(sum([x[0] for x in L]))
    return [x[0]/V for x in L]

def ppebwr_total_probs(p,t):
    """
    Return 'total probabilities' (of being selected) by
    ppebwr method with t rounds.
    """
    return [(1.0-(1.0-x)**t) for x in p]

#####################################################################
### older stuff... unused...
#####################################################################

def evaluate(L,k,margin,p,w):
    """
    print an evaluation of negexp strategy
    L is list of all n precincts
    k is the number of precincts to be sampled
    margin is the margin of victory (as a fraction)
    p is probability vector for negexp approach
    w is negexp precinct size threshold
    """
    n = len(L)
    V = sum([prc[0] for prc in L])
    V2 = sum([prc[0]**2 for prc in L])

    max_shift_per_precinct = 0.20
    shift_factor = 1.0 / (2.0 * max_shift_per_precinct) # 2.5
    C = shift_factor * margin *V             # number of votes in corrupted precincts

    print
    print "Evaluation of negexp strategy"
    print "For margin of victory m=%0.4f (as a fraction)"%margin
    print "Assumes that adversary will shift at most fraction s=%0.2f of votes in precinct."%max_shift_per_precinct
    print "Assumes that adversary shifts C=%0.2f votes."%C
    print
    print "For negexp auditing strategy shown above:"
    print "  Confidence of detecting fraud that could have changed winner at least:",
    detection_prob = 1 - math.exp(-C/w)
    print "%0.2f percent"%(100*detection_prob)
    print "  Negexp threshold w = ",w,"votes"
    negexp_workload = sum([L[i][0]*p[i] for i in range(len(L))])
    print "  Expected number of votes to be audited:",negexp_workload
    negexp_precincts = sum([p[i] for i in range(len(L))])
    print "  Expected number of precincts to be audited:",negexp_precincts

    # Against adversary strategy using optimal strategy against uniform strategy
    # which is to corrupt the largest precincts only
    # probabilistically, to get expected number of votes in corrupted precincts = C
    print
    print "For uniform auditing strategy with same number (%d) of precincts audited:"%k
    print "  (Auditor picks precincts independently with probablity %0.4f)"%(float(k)/float(n))
    print "  (Assumes adversary corrupts largest precincts first.)"
    print "  Confidence of detecting fraud that could have changed winner:",
    miss_prob = 1.0               # probability of missing detection
    votes_tobe_corrupted = C
    precincts_corrupted = 0
    uniform_workload = 0.0
    for prc in L:
        vi = float(prc[0])
        pi = float(k)/float(n)
        uniform_workload += pi*vi
        if votes_tobe_corrupted > 0:
            qi = min(votes_tobe_corrupted/vi,1.0)
            votes_tobe_corrupted -= vi
            precincts_corrupted += 1
        else:
            qi = 0.0
        miss_prob *= (1.0 - pi*qi)
    detection_prob = 1 - miss_prob
    print "%0.2f percent"%(100*detection_prob)
    print "  Precincts corrupted:",precincts_corrupted
    print "  Number of precincts to be audited:",k
    print "  Expected number of votes to be audited:",uniform_workload

    # One more analysis, against an auditing
    # strategy that is uniform but with the same expected workload
    # (number of votes audited) as the negexp strategy.
    print
    print "For uniform auditing strategy with about same workload as negexp:"
    print "  (Auditor picks precincts independently with probability %0.4f)"%\
          (float(negexp_workload) / float(V))
    print "  (Assumes adversary corrupts largest precincts first.)"
    print "  Confidence of detecting fraud that could have changed winner at least:",
    miss_prob = 1.0               # probability of missing detection
    votes_tobe_corrupted = C
    precincts_corrupted = 0
    new_uniform_workload = 0.0
    new_uniform_precinct_count = 0.0
    for prc in L:
        vi = float(prc[0])
        pi = float(negexp_workload) / float(V)
        new_uniform_workload += pi*vi
        new_uniform_precinct_count += pi
        if votes_tobe_corrupted > 0:
            qi = min(votes_tobe_corrupted/vi,1.0)
            votes_tobe_corrupted -= vi
            precincts_corrupted += 1
        else:
            qi = 0.0
        miss_prob *= (1.0 - pi*qi)
    detection_prob = 1 - miss_prob
    print "%0.2f percent"%(100*detection_prob)
    print "  Precincts corrupted:",precincts_corrupted
    print "  Expected number of precincts to be audited:",new_uniform_precinct_count
    print "  Expected number of votes to be audited:",new_uniform_workload


def main():
    """
    main procedure
    """

    if len(sys.argv)!=4:
        print """Usage: varsize.py k filename margin
    where  (optional) k  is the desired number of precincts to be selected
        If no k given, defaults to k=2.
    where (optional) filename has one line per precinct:
        Each line has the form: 'size,precinct_name'  (e.g.  40, Cambridge  )
        where size is an positive integer 
        where precinct_name is optional (and may have blanks)
        If no filename given, defaults to four precincts 40 A, 30 B, 20 C, 10 D.
        filename can also be a string that constructs the list directly, e.g.
          "['500,']*53 + ['41,']*144 + ['7,']*144"
        represents 53 precincts of size 500, 144 of size 41 and 144 of size 7.
        For this it should include the ']' character, and it will be passed
        to eval.
    where (optional) margin gives fraction of the margin of victory (e.g. 0.02)
        If positive margin given, prints some confidence levels.
        If no margin given, defaults to 0.02
    """
    if len(sys.argv) <2:
        k = 2
        print "No k given; using default k=2."
    else:
        k = int(sys.argv[1])
        print "k =",k,"precincts to be selected."

    if len(sys.argv) < 3:
        lines = ["40,A,","30,B,","20,C,","10,D,"]
        print "No filename given; using following test file:"
        for line in lines: print "   ",line
        L = make_precinct_list(lines)
    else:
        file_name = sys.argv[2]
        print "File name:",file_name
        if file_name.find("]"):
            lines = eval(file_name)
            for line in lines: print "   ",line
            L = make_precinct_list(lines)
        else:
            L = read_precincts(file_name)

    assert k<=len(L)

    if len(sys.argv) < 4:
        margin = 0.02
        print "No margin given. Defaulting to 0.02 (two percent)"
    else:
        margin = float(sys.argv[3])   # fraction
        print "Margin of victory = %0.4f (fraction)"%margin

    print_precinct_stats(L)
    V = sum([x[0] for x in L])

    ### Choose one of these three; comment out the others
    p,w = negexp_probs_for_confidence(L,margin*2.5*V,0.08)
    # p,w = negexp_probs_for_workload(L,A)    # where does A come from?
    # p,w = negexp_probs_for_number_of_precincts(L,k)

    print "w = ",w
    print "p = ",p

    evaluate(L,k,margin,p,w)

import matplotlib.numerix as nx
import pylab

def plotprobs(title,p):
    pylab.plot(p, color='red', lw=4)
    pylab.title(title)
    pylab.show()

def paper(source,title,m,alpha=0.08,s=0.20):
    """
    Compute results mentioned in our paper.
    m = margin of victory (as a fraction)
    alpha = significance level desired = 1 - confidence
    s = maximum within-precinct miscount
    Return a dictionary with the main results.
    """

    results = {}

    print
    print "Contest:", title
    L = read_precincts(source)
    print_precinct_stats(L)
    v = [x[0] for x in L]
    n = len(v)
    V = sum(v)
    ave = float(V)/n
    M = m*V
    print "margin = ",m*100.0,"percent,",M,"votes"
    print "s = ",s, " (maximum within-precinct-miscount)"
    print "alpha = ",alpha, " (confidence is 1 - alpha: ", 1.0-alpha, ")"
    print
    print "Rule of Thumb says:"
    if m != 0.0:
        print "   ",1.0/m,"precincts."
        A = ave*int(math.ceil(1.0/m))
        print "    expected workload = ",A,"votes counted."
    else:
        print "   ",n,"precincts."
        print "    expected workload = ",V,"votes counted."
    print
    print "APR says:"
    u = APR(n,m,alpha,s)
    u = int(math.ceil(u))
    b = M / (2.0 * s * ave)
    print "    b =",b,"precincts needed to hold corruption"
    print "    u = ",u,"precincts to audit"
    print "    expected workload = ",u*ave,"votes"
    print "    confidence level to find one of b = ",confidence_for_uniform_audit(n,u,b)
    bm = bmin(L,M)
    print "    bmin =",bm
    print "    confidence level to find one of bmin = ",confidence_for_uniform_audit(n,u,bm)
    print
    print "SAFE says:"
    bm = bmin(L,M)
    print "    bmin =",bm
    if bm != 0:
        u = (n - (bm-1)/2.0)*(1.0-math.pow(alpha,1.0/bm))
        u = int(math.ceil(u))
    else:
        u = n
    print "    Number of precincts to audit = u =",u
    c = confidence_for_uniform_audit(n,u,bm)
    print "    Confidence level achieved = ",c
    print "    expected workload = ",u*ave
    results.update({'safe_precincts': u, 'safe_work': u*ave, 'safe_confidence': c})

    print
    print "Negexp says:"
    pn,wn = negexp_probs_for_confidence(L,M,alpha,s)
    print "    w =",wn
    print "    largest probability = ",pn[0]
    print "    smallest probability = ",pn[-1]
    u = sum(pn)
    print "    expected number of precincts audited = ",u
    A = sum([pn[i]*v[i] for i in range(n)])
    print "    expected workload = ",A,"votes counted"
    results.update({'negexp_precincts': u, 'negexp_work': A, 'negexp_confidence': None})

    if __name__ == "__main__":
        plotprobs(title,pn)
    print
    print "PPEBWR says:"
    E = 2.0*s*V
    t = math.log(alpha)/math.log(1.0-max(0.00000001, min(M/E, .999999)))
    t = int(math.ceil(t))
    print "    t = ",t
    pt = [(1.0-(1.0-float(v[i])/V)**t) for i in range(n)]
    print "    largest total probability = ",pt[0]
    print "    smallest total probability = ",pt[-1]
    print "    expected number of precincts audited =",sum(pt)
    A = sum([pt[i]*v[i] for i in range(n)])
    print "    expected workload = ",A,"votes counted."
    results.update({'ppebwr_precincts': sum(pt), 'ppebwr_work': A, 'ppebwr_t': t})
    maxdev = max([abs(pn[i]-pt[i]) for i in range(n)])
    print "    max difference from negexp = ",maxdev

    return results

# paper("oh5votesonly.txt","Ohio 2004 CD-5",0.01)
# paper("MN_Gov_2006-2.csv","Minn 2006 Governors Race",0.0096)
# paper("120x100-precincts.csv","120 batches of 100 ballots",0.01)

if __name__ == "__main__":
    main()
