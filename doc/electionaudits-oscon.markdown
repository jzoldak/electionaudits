ElectionAudits talk for OSCON - 2009-07-22
by [Neal McBurnett](http://neal.mcburnett.org/)

# ElectionAudits: a Django App for Advanced Election Auditing
* Boulder County used open source code to audit its 2008 election!
* Share the story, share the code, and get you all involved where you live.

* Why audit?
* Elections to celebrate: South Africa 1994, paper ballots, hand counted
* Obvious disasters: Iran 2009 - clearly fraudulent [Preliminary Analysis of the Voting Figures in Iran's 2009 Presidential Election](http://www.chathamhouse.org.uk/publications/papers/view/-/id/755/)
* US problems with elections: black box voting systems
* Not just a problem with touch screen devices (DRE)
* Humboldt County 2008: 197 ballots deleted by Diebold/Premier without a trace.
* Certified
* Discovered later by Humboldt County Election Transparency Project audit

* Goal: software independence, via auditable paper records, good audits
* Open Source voting systems: Great!
* Good audits and chain of custody: Necessary

fascinating algorithms behind modern election auditing,
  negexp, ssr, 
  Rivest's Sum of Square Roots method

# How - what is an audit anyway?
* Audit Election: Compare sample of detailed results with hand counts
* Auditing hand-counted election:
** Count piles of ballots by hand and write subtotals down
** add them up
** check arithmetic and compare to number of ballots
* Optical scanners arrived: era of trusting computers too much
* Audit DREs without voter verified paper trail?  Can't do it....  Pushback.
* Audit optical scan systems, e.g.[Markey vs Musgrave](http://bcn.boulder.co.us/~neal/elections/boulder-audit-08-11/reports/4/)
* Closing loopholes and gaps; Getting more efficient,  Improved confidence in election outcomes
<!-- in Boulder than anywhere but a few California counties which also had good audits
. and Minnessota and ?? -->
* Map of how audits vary by state: (from ea web site)
* Fixed percentage vs Risk-limiting audits
* [Selections for Markey vs Musgrave](http://bcn.boulder.co.us/~neal/elections/boulder-audit-08-11/selections/4/)
* [Principles and Best practices](http://electionaudits.org/principles/)
* Results

# Django and Python
* Rivest's varsize.py
* ElectionAudits - MIT license
* Hosted at Launchpad, Bzr
* Debug_toolbar for great debugging over the web

# Help wanted with:
* Web presentation: css, layout
* Logo
* XML expertise, e.g. for reading and writing (and improving) Election Markup Language
* Database design
* Django/python insights
* Implement features
* Windows testing, installation, eggs and Django, etc
* Help getting auditing laws passed.  c.v. Colorado - Election Reform Commission
* Biggest challenge: getting useful data out of election systems

* At 1:45: _Open Source and Democracy - Creating transparent, trustworthy voting systems_
* Code is Law - Write our own procedures (after randomness cluelessness)

# Links:
* [ElectionAudits on Launchpad](https://edge.launchpad.net/electionaudits)
* [Boulder Audit, 2008](http://bcn.boulder.co.us/~neal/elections/boulder-audit-08-11/)
* (https://edge.launchpad.net/electionaudits)
* [Help Audit Elections](http://neal.mcburnett.org/blog/2008/10/18/electionaudits-software-help-audit-election/)
* [Open source auditing tool boosts election integrity](http://arstechnica.com/news.ars/post/20081221-open-source-auditing-tool-boosts-election-integrity.html) -  ArsTechnica

This talk: <http://bcn.boulder.co.us/~neal/electionaudits/electionaudits-oscon.html>
