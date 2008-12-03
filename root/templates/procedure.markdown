<title>Procedure - Boulder County 2008 General Election Audit</title>

<p> <a href="/~neal/elections/boulder-audit-08-11/">Home</a> </p>

Boulder County Audit Procedure, November 2008
=============================================

Boulder's audit plan was designed to bring the
[Principles and Best Practices for Post-Election Audits](http://electionaudits.org/principles/)
to bear on Colorado elections.

It makes much better use of the amount of work that Colorado law
generally calls for in audits.  It audits the same total number of
audit units that other counties were required to audit - one per
contest.  In other counties that was spread out over 5% of the
machines, and mail-in and central count ballots were treated specially
and audited far less.  Boulder treated centrally counted and mail-in
ballots the same as others, which led to more total ballots being
counted.

We obtained prior approval from the Secretary of State's office for
doing this enhanced audit.

## Synopsis

It is important to do the steps in the audit in the proper sequence.
In particular, the reports to be audited must be published before
the selections or counting begins.  These were the steps:

 * Gather necessary batch-by-batch data during the original scanning.
 * Feed that data into the ElectionAudits software, which automatically
  produced and published the [reports](../reports/) on this web site, with
  full results for each contest for each of the 525 batches of ballots.
 * Roll 15 dice, which ElectionAudits used to determine
  the [selections](../selections/): both contests to be audited, and
  exactly which batches to audit for each contest.
 * Retrieve the paper ballots and start tallying votes by hand.
 * Study the published data, take input from the public, and
 target additional audit units as appropriate.
 * If there are significant discrepancies, audit additional audit units.
 * Report the [results](../results/).

The descriptions below may seem complicated in places, but remember
that the complicated parts are handled automatically by the open source
ElectionAudits software.

Publishing Auditable Data
=========================

It is very important for the transparency of the audit to publish
detailed audit reports, with full election results on each audit unit
(a batch, precinct or DRE machine), before the audit or random
selection is done.

We did this via the open source ElectionAudits software.  It read in
cumulative xml reports that were produced by election staff during the
original tally for each of the 525 audit units.  There was one cumulative
report for each Mobile Ballot Box (MBB) that was fed into the Hart
InterCivic tally system.

Then we published that data on the web site:

 <http://bcn.boulder.co.us/~neal/elections/boulder-audit-08-11/>

Random numbers for selection
============================

The contests to audit, and audit units within the contests, were
selected randomly.  We started the random selection by throwing dice
to generate a random "seed".  The procedure was designed so that even
if observers distrusted all but one of the people throwing the dice,
they would still know that the entire random selection procedure would
incorporate a significant amount of randomness from the dice thrown by
the one person they trusted.  See the papers referenced below for
more background.

First we gave a sheet of paper to each participant, and assigned each
a participant number between one and five.  Each participant then
threw three differently colored translucent 10-sided dice in private,
and wrote down the numbers showing on the dice in the order 1) grey 2) yellow
3) blue on the piece of paper and folded it over.  Finally we brought
the papers back, unfolded them and entered the numbers in order into
the ElectionAudits software.  The 15 digits of the random seed were
702758241994347 (e.g. the first person's throws were grey: 7, yellow:
0 and blue: 2).

Next we used the "Sum of Square Roots" (SSR) pseudorandom number generator
(see the references below) to generate pseudorandom numbers for each
of the 525 batches.  The number for each batch is based on both the
batch sequence number and the random seed from the dice.  We also used
it to generate random numbers for the selection of the contests to be
audited.

The great thing about SSR is that it is how transparent it is.  It is
easy for anyone to verify the random numbers that are assigned to each
batch with nothing more than a calculator.

For example, here is how to use the random seed we rolled to verify
the random number for the top batch in the [State Representative -
District 33 race](../selections/13/).  As you see at the top of that
page, the first batch has a batch sequence number of 000149, and is
named "p174_mb_152".  The SSR method mixes the random dice throws with
the sequence number like this.  Take the first two digits of the
sequence number (00) and the first 5 digits of the random seed (70275)
to make the number 0070275, and enter that into a calculator.  Hit the
square root key, and get 265.094322.

Hit the "+" key and then do the same with the next two digts of the
batch sequence (01) and the next five digits of the seed (82419).  The
square root of 0182419 is 427.105373, and hitting plus again yields
692.199696.

Finish by doing the same steps one more time with the remaining
digits.  Sqrt(4994347) is 2234.803570, and hitting "+" one more time
(or "=") shows the final sum: 2927.003267.  The fractional part is the
random number we're looking for: 0.003267, and that is the number
shown in the "Random" column.  It is a low number, which gives this
batch a high probability of selection as we'll see below.

Note: since it is derived via a formula, it is not really a random
number, like the random seed from the dice.  It is a "pseudorandom"
number, but as discussed in the references, it is unpredictable and
varied enough for our purposes, and we'll generally use the the term
"random" as a shorthand.  You can see how much difference the dice rolls
make by looking at the
[same race with a different random seed](../selections-example/13/).
The big batches still tend to show up at the top, as desired, but
are in a very different order.

Selection proportional to size: NEGEXP
======================================

As discussed in the paper [On Auditing Elections When Precincts Have Different Sizes](http://people.csail.mit.edu/rivest/AslamPopaRivest-OnAuditingElectionsWhenPrecinctsHaveDifferentSizes.pdf), audits can achieve much more confidence for a given amount of effort
if the audit units are selected in proportion to their size.  The Boulder
audit used the "NEGEXP" method from that paper.  It
has the additional benefit of sharing the same batch for multiple audit units,
which can also make the counting and paper handling more efficient.

When using NEGEXP, a threshold is first assigned to each batch.  The
threshold is larger for larger audit units, based on the "negative
exponential" of the size, as discussed in the paper.  The pseudorandom
number calculated for the batch is then compared to the threshold. The
larger the threshold in comparison to the random number, the more
likely the unit is to be selected. The "Priority" in the tables of
audit units is the threshold divided by the random number, so the
priority is larger for larger thresholds (larger batches), or for
lower random numbers.  The audit selections are then chosen in decreasing
order by priority.  Incorporating the random number in the priority
keeps us us from invariably auditing only the largest batches, which
would make it easy for an adversary to know which batches to avoid.

In the example above, the threshold is 0.026777, and when that is
divided by the random number for the batch (0.003267) we get the
priority, 8.196011, which is greater than any of the other audit units.

Note: In our procedure, we used the "expected number of precincts
audited" that was calculated for the NEGEXP method and took that many
batches in priority order (rounding the number up to be conservative).
The normal NEGEXP procedure is to instead simply select all audit
units for which the threshold is greater than the random number.  That
would be better, but requires some updates to the software to
calculate the thresholds appropriately when there are audit units
outside of the county and the proportion is less than 100%.

Contest Selection
=================

We wanted to put the 65 audit units to good use by doing more
efficient and effective "risk-limiting" audits, which audit multiple
audit units for close contests.  Given that we would audit 65
contests, that meant that not every contest would be audited in
Boulder, but the random contest selection procedure ensured that every
contest would still stand a chance of being audited.

We needed the overall margin of victory for all of the contests.  This
data should incorporate under votes and over votes.  ElectionAudits
automatically generates proper margins for contests that are entirely
within the county.  But we actually can't find all this data for wider
races aggregated anywhere, so we used estimates from newspaper web
sites.  Amazingly, the best data came not from local newspapers, but
from usatoday.com, where the data was easier to copy and paste than it
was from most web sites.

We then selected the contests.

We decided to be certain to audit the presidential race.

We then randomly chose 10 other contests for risk-limiting audits: 6
state-wide, and 4 local or regional.

We weighted the contest selection probabilities by the inverse of the
margin.  So a contest with a 2% margin would be 10 times as likely to
be selected as one with a 20% margin.  These are likely to be the
contests of greatest interest also.  In the future we will consider
incorporating a measure of citizen interest like the fraction of
undervotes for each contest, or number of total valid votes.  We
assigned 1/margin as priority values to each contest, assigned random
numbers to each one as in the NEGEXP method, divided the priority by
the random numbers, sorted the contests by priority, and chose the top
races for each category.

Audit Unit Selection
====================

We determined a desired level of "confidence", assuming a 20% maximum
within-precinct-miscount (WPM) as discussed in the NEGEXP and SAFE
papers:

 * State contests: 99% confidence

 * Local contests: 75% confidence desired, but with a cap of 10 random
 audit units per contest

Without the cap of 10, one contest could require all 65 units and we
wouldn't be able to audit any other contests.  Given the number and
size distribution of audit units in Boulder, that limit on 10 audit
units is equivalent to saying we'll audit to 75% confidence for races
down to about a 5% margin, but achieve less confidence for tighter
ones.

Note that these "confidence" levels are subject to interpretation.

On the one hand, the numbers are very conservative.  They apply not
only to cases where there are software bugs, but also to cases where
an adversary has total control over the tally computers, and can
report any tallies for any audit units.  Of course there are security
controls in place, bonding of employees, testing of code, etc. etc. so
that is very rarely the case, and confidence in election outcomes is
generally far higher than the confidence given here.

On the other hand, some statisticians don't think the 20% WPM
assumption is warranted, even given that we allowed for audit units to
be targeted if they did not seem to fit within this assumption.  We
also calculated the size for weighting the selections based on
just the "contest ballots", even when those
contest ballots were infrequent in a given batch.  And we applied the WPM
ot that same size.  The canvass
procedures should validate how many valid ballots for a given contest
went in to each batch.  Otherwise an adversary could set the results
for a given batch to zero for a contest and thus make it very unlikely
to be selected.  That level of canvassing was not done for this
election.  So the level of confidence may be overstated,
especially for contests that were not on all the ballots in the county.
For a more rigorous and conservative approach, see
<a href="http://statistics.berkeley.edu/~stark/Vote/index.htm">
Philip B. Stark, Papers and Talks on Voting and Election Auditing</a>.

Based on the margin and confidence level, we determined how many audit
units to select for each contest.  In contests that extended outside
the borders of Boulder County, we audited our share of the total
number pro-rated by the proportion of the ballots cast in Boulder
County.  Note that we had the same difficulty obtaining good numbers
for these proportions as we did for the margins.

If the total number of audit units to be randomly selected for the 11
contests was less than 65, and if some of the contests had been capped
at 10 audit units as noted before, we planned to relax the caps and
add more audit units for the contests in order to bring up the minimum
confidence level to as close to 75% as possible.

If the number was still less than 65, add additional contests in
priority order as before.  In this election, we added two more
contests.

The Canvass board also has the discretion to target suspicious audit
units based on their own insights or public input received by Nov
18th.  This helps with the 20% minimum WPM assumption and can be used
to address specific issues like scanning problems or general process
improvement.

Method of Hand Counting
=======================

If there is a machine recount required based on < 0.5% margin or if
someone eligible wants to pay, we face an additional difficulty.  Our
ballots are generally 4 pages (2 sheets, back-to-back), 11 x 17".  But
each ballot has a unique sequence number, and our version of the the
Hart BallotNow system rejects ballots that come out of sequence,
forcing operators to find matching pairs and re-scan.  This is
reportedly fixed in more recent versions of the software.

So it would be risky to hand count the ballots by sorting them in to
piles and keeping the pairs together.  It would be problematic to have
to match all the ballot back together.

As a result, we audited via the "announce and tally" method, rather
than the "sort stack and count" method, even though it is generally
considered to be less accurate.

As usual, the hand counters did not know what the machine tallies were
when they did their counts.  The counters tallied each audit unit
twice.  We told the counters to not worry too much about a discrepancy
of one or two in their counts.  But if their two counts were off by
more than two, they recounted until they got two similar tallies.

In a few cases, when we checked their tally against the machine tally
it differed by more than two.  In the case of one batch (with two
audit units), it turned out that we had not given them three ballots
that should have been included in their pile of ballots, and that made
the difference.  In another case, we found that another hand count
(again without knowing the machine count) came up with a match.  And
in another case we tracked it down to a mistake with one overcount in
the manual resolution process during the original machine tally.

The remaining small differences in the machine and manual tallies
might be due either to the difficulty of the hand count method and the
instructions to not ensure that counts match, or to other infrequent
problems with the machine count.  But even so we can have more
confidence in the results than ever before, especially for the close
contests that were audited.  Given more time for analysis, and with
the added experience we now have, and improvements in the software and
hand tally methods, we will be able to do even better in the future.

Addressing Discrepancies
========================

If there are significant discrepancies for a given contest, audit
additional audit units, escalating to a full recount if the outcome
is significantly in doubt.
<em>Note: this part of the description of the procedure is not yet finished.</em>

References
==========

 * [On Auditing Elections When Precincts Have Different Sizes](http://people.csail.mit.edu/rivest/AslamPopaRivest-OnAuditingElectionsWhenPrecinctsHaveDifferentSizes.pdf) by Aslam, Popa and Rivest.
 * [A "Sum of Square Roots" (SSR) Pseudorandom Sampling Method For Election Audits](http://people.csail.mit.edu/rivest/Rivest-ASumOfSquareRootsSSRPseudorandomSamplingMethodForElectionAudits.pdf) by Ronald L. Rivest.
 * [In Defense of Pseudorandom Sample Selection](http://www.usenix.org/event/evt08/tech/full_papers/calandrino/calandrino_html/) by Joseph A. Calandrino, J. Alex Halderman, and Edward W. Felten.

Lessons
=======

It is very hard to get state-wide results for the contests with the
necessary counts for under votes and over votes.  The Secretary of
State should gather these starting on election night and publish it
on their web site, so we don't have to rely on newspaper reports.
