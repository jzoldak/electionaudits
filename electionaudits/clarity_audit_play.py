    """
    # Code to take 749 talles from 2016, via mix of clarity and electionaudits code, and
     summarize it
     get concise county names
     fix contests with multiple winners;
     augment tally data: list which counties each contest is in
     invert that list / index(?): produce contests for each county
      [should combine those two...]
     save as json
    """

    import electionaudits.models as models

    st = []  # tallies  aka res
    for contest in models.Contest.objects.all():
      print contest
      st.append(contest.tally())

    for stats in st:
      print >> o , "%(contest)-34.34s: %(total)8d %(winnervotes)8d %(winner)-8.8s %(secondvotes)8d %(second)-8.8s  %(margin)6.2f%%" % stats

    s = sorted([(c['margin'], c) for c in st])
    [cb.batch.name[42:-4] for cb in cbs if cb.contest == d6]
    [u'Adams', u'Arapahoe', u'Douglas']

    cbs = list(models.ContestBatch.objects.all())  # contestsInCounties

    con = contests[0]  # president
    allcounties = [cb.batch.name[42:-4] for cb in cbs if cb.contest == con]

    for r in res:
       r['counties'] = [cb.batch.name[42:-4] for cb in cbs if cb.contest.name == r['contest']]

    countiesbymargin = []
    for county in allcounties:
        countycontests = []
        for r in res:
            if county in r['counties']:
                countycontests.append(r)
        countiesbymargin.append(sorted(countycontests, key=lambda c:c['margin']))

    ?? with open(...) as o:
      for (county, countycontests) in zip(allcounties, countiesbymargin): 
        print >> o, county
        for r in countycontests[0:3]:
           print >> o, "  %(margin)6.2f%% %(total)8d %(winnervotes)8d %(winner)-8.8s %(secondvotes)8d %(second)-8.8s  %(contest)-34.34s" % r

    for (county, countycontests) in zip(allcounties, countiesbymargin):                                                            
        r = countycontests[0]
        o.write("%-15.15s %s\n" % (county, "%(margin)6.2f%% %(total)8d %(winnervotes)8d %(winner)-8.8s %(secondvotes)8d %(second)-8.8s  %(contest)-34.34s" % r))

    export as json

    what I really want is to add size of county in ballots, drop state-wide races entirely,
     and for now just include just county races
     just drop all multi-county cb's....
     include absolute margin, not just percent margin

     e.g. define numballots(county) = number to audit based just on county-only contests
      print those out
      then for each contest
        and how many would be needed in each county, proportionally
        compare to how many would be counted for it based on county counts [taking into account fraction of county]

