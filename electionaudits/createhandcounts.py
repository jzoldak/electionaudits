from electionaudits.models import *

choices = ['Emma R. Hall', 'Daniel H. Pruett', 'Over', 'Under']

handcounts = [
 ('p255', [137, 69, 0, 91]),
 ('p238', [108, 130, 0, 62]),
 ('p371', [118, 66, 0, 102]),
 ('p377', [145, 44, 1, 109]),
 ('p118', [98, 105, 1, 87]),
 ('p029', [133, 88, 0, 78]),
 ('p078', [113, 96, 0, 87]),
 ('p379', [119, 59, 0, 116],
  )]
handcounts2 = [
 ('p337', [147, 60, 0, 107],
  )]

def createhandcountbatch(election, contest, batch, choices, votecounts):
    e = CountyElection.objects.get(name=election)
    c = Contest.objects.get(name=contest, election=e)
    b = Batch.objects.get(name__startswith=batch, election=e, type="U") # , defaults={'ballots': ballots}
    contest_batch = HandContestBatch.objects.create(contest=c, batch=b)
    for (choice, votes) in zip(choices, votecounts):
        choice = Choice.objects.get(name=choice, contest=c)
        HandVoteCount.objects.create(choice=choice, votes=int(votes), contest_batch=contest_batch)

def main():
    election = "Boulder-2010-General"
    contest = "COUNTY CORONER Vote For 1"
    
    print "%d new handcount batches" % len(handcounts2)

    for batch, hcs in handcounts2:
        createhandcountbatch(election, contest, batch, choices, hcs)
        print "%s: %s" % (batch, hcs)

main()

sys.exit(0)

from cStringIO import StringIO

[('CNGREP', lungren), ('CNGDEM', durston), ('CNGLIB', tuma), ('CNGPAF', padilla)]

handcounts = StringIO('''06005AV130,424,231,149,13,12,1,230,150,13,12
06005CP01,447,244,152,15,15,2,244,152,15,15
06005CP16,319,159,115,15,12,1,159,115,15,12
06009350,919,440,392,30,16,2,442,393,30,16
06009430,990,493,377,34,30,1,493,377,34,30
06009520,990,528,332,34,33,2,528,332,36,33
06009535,1119,597,393,35,39,1,597,393,35,39
0606721310,440,152,197,4,35,1,152,197,4,35
0606722716,644,254,294,9,25,1,254,294,9,25
0606726108,685,290,284,14,36,2,290,284,14,36
0606726420,382,158,172,14,15,1,158,182,14,15
0606728102,685,260,316,23,27,1,260,316,23,27
0606728312,710,290,323,22,25,1,290,323,22,25
0606731404,628,294,228,13,36,1,294,228,13,36
0606733224,684,387,220,10,9,1,387,220,10,11
0606734106,623,238,257,25,32,1,238,257,25,32
0606736740,670,289,266,20,23,1,289,266,20,23
0606755800,688,274,301,12,34,1,274,301,12,34
0606757750,381,202,118,11,24,1,202,118,11,24
0606758200,706,402,210,10,30,1,403,211,10,30
060678022102,467,216,182,13,15,1,216,182,13,15
060678023118,579,247,247,14,34,1,247,247,14,34
060678023126,442,215,163,16,21,1,215,164,16,21
060678023624,436,168,180,21,27,1,168,180,21,27
060678024324,417,201,156,12,14,1,201,156,12,14
060678025810,435,164,224,9,18,1,164,224,9,18
060678029102,736,323,330,19,26,1,324,334,19,26
060678031132,724,359,270,14,22,1,359,270,14,22
060678031204,538,297,166,13,23,1,297,166,13,23
060678052200,527,217,247,15,21,1,217,247,15,21
060678053126,444,204,185,13,16,1,204,185,13,16
060678057156,716,364,285,8,17,1,364,285,8,17
060678057206,591,279,246,13,14,1,279,246,13,14
060678057620,544,291,195,12,13,1,293,196,12,13
060678061100,1020,570,395,14,12,1,570,395,14,12
060678061130,863,474,330,16,6,1,474,330,16,6
060678089318,537,261,191,10,40,1,261,191,10,40
0606782030,592,162,309,5,50,1,162,309,5,50
0606787344,338,186,86,7,15,1,186,86,7,15
0606789318,606,313,174,17,43,1,313,174,17,43
0609549700A,634,336,229,26,21,2,336,229,26,21
0609594939,209,105,80,4,6,1,105,80,4,6
''')

# input data:   CNGREP CNGDEM CNGLIB CNGPAF
# alphabetical: CNGDEM CNGGRN CNGLIB CNGPAF CNGREP

        # 0606724312  dem 9	0	0	2	rep 12	3

000051	0.945350	0606781448	255	0.016330	0	102	0	3	5	132	13

0606781448	255	102	0	3	5	132
0606781448	255	102	0	3	5	132
0606781448	255	132     102	3	5	
0,0,0,0,1, 

000052	0.005173	06005AV103	337	0.019366	0	147	0	9	13	148	20
000053	0.231381	0606723710	610	0.034321	0	251	0	14	46	240	59
000054	0.322367	0606728606	506	0.034665	0	176	0	8	14	275	33
000055	0.619219	060678025430	538	0.030023	0	248	0	9	15	234	32
000056	0.422998	0606737312	530	0.036212	0	185	0	12	11	287	35
000057	0.176488	0606722120	568	0.034034	0	212	0	5	18	238	95

election="Kaplan-example"

contest="Congress03"

# make this a transaction.

for l in handcounts.readlines():
    (batch, ballots, _,_,_,_, times, lungren, durston, tuma, padilla) = l.split(',')
    e = CountyElection.objects.get(name=election)
    c = Contest.objects.get(name=contest, election=e)
    b = Batch.objects.get(name=batch, election=e, type="U") # , defaults={'ballots': ballots}
    contest_batch = HandContestBatch.objects.create(contest=c, batch=b)
    for (choice, votes) in [('CNGREP', lungren), ('CNGDEM', durston), ('CNGLIB', tuma), ('CNGPAF', padilla)]:
        choice = Choice.objects.get(name=choice, contest=c)
        HandVoteCount.objects.create(choice=choice, votes=int(votes), contest_batch=contest_batch)

c.election.random_seed = '123456789012345'
c.election.save()

'''
"ballots",,,,,"times","audit","audit","audit","audit","e_ e_Tuma",,"taint =","KM factor net KM"
"precinct","cast","Lungren"," Durston","Tuma","Padilla","drawn","Lungren","Durston","Tuma","Padilla","Durston ","e_Padilla","max(e) / up","         factor"
'''
