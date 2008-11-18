import os
import math
import operator
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from electionaudits.models import *
import electionaudits.parsers

class Empty:
    "Emtpy class for holding arbitrary information"

    pass

def report(request, contest):
    """Generate audit report for all ContestBatches and VoteCounts
    associated  with the contest"""

    contest = get_object_or_404(Contest, id=contest)

    stats = contest.stats()

    audit_units = contest.select_units(stats)

    """
    display calc for "overall margin"
    {%if proportion is 100%, use margin
    else if missing, say <strong>MISSING</strong>
    else
    {{ object.overall_margin|floatformat:3 }}%
    """

    return render_to_response('electionaudits/report.html',
                              {'contest': contest,
                               'contest_batches': audit_units,
                               'stats': stats } )

def results(request):
    """Generate results list for all selected audit units"""

    selected=[1,  35, 34, 42, 51, 37, 48,   13, 61, 58, 62, 63, 59 ]

    audit_units = []
    for contest_id in selected:
        contest = get_object_or_404(Contest, id=contest_id)

        stats = contest.stats()

        audit_units += contest.select_units(stats)[0:min(10, int(math.ceil(stats['negexp_precincts'])))]

    # Add in targetted audit units
    # Note contests that have a bit of auditing, and those that are
    # audited to less than the rated confidence level.

    targeted = list(ContestBatch.objects.filter(selected=True).order_by('contest__id'))

    # Take out any that were already selected - don't double-count
    for au in set(targeted) & set(audit_units):
        targeted.remove(au)

    audit_units += targeted

    batchset = set(au.batch for au in audit_units)

    s = Empty()

    # FIXME: get ballot counts from pdfs
    # for now just add one for the number of ballots with no "president" contest
    # i.e. the absentee land owners voting on property taxes but not president
    s.ballots = 1 + sum(b.ballots or 0  for b in Batch.objects.all())
    s.contests = len(Contest.objects.all())
    s.batches = len(Batch.objects.all())
    s.audit_units = len(ContestBatch.objects.all())
    s.votes = sum(au.contest_ballots() for au in ContestBatch.objects.all())
    s.votes_per_ballot = 1.0 * s.votes / s.ballots

    s.contests_selected = len(selected)
    s.contest_pct = s.contests_selected * 100.0 / s.contests

    s.audit_units_selected = len(audit_units)
    s.audit_units_pct = s.audit_units_selected * 100.0 / s.audit_units

    s.batches_selected = len(batchset)
    s.batches_pct = s.batches_selected * 100.0 / s.batches

    s.ballots_selected = sum(b.ballots for b in batchset)
    s.ballots_selected_pct = s.ballots_selected * 100.0 / s.ballots

    s.votes_audited = sum(au.batch.ballots for au in audit_units)
    s.votes_audited_pct = s.votes_audited * 100.0 / (s.votes)

    s.targeted = len(targeted)
    s.targeted_pct = s.targeted * 100.0 / s.audit_units

    return render_to_response('electionaudits/results.html',
                              {'contest': contest,
                               'contest_batches': audit_units,
                               's': s } )

@staff_member_required
def parse(request):
    """
    A form that lets an authorized user import and the parse data files in
    the incoming directory.
    """

    dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'incoming')

    if request.method == 'POST':
        parse_form = forms.Form(request.POST)
        if parse_form.is_valid():
            options = electionaudits.parsers.set_options(["-c", "-s"])
            electionaudits.parsers.parse([dir], options)

    else:
        parse_form = forms.Form()

    return render_to_response('electionaudits/parse.html', {
        'parse_form': parse_form,
        'parse': os.listdir(dir)
    })


class StatsForm(forms.Form):
    margin = forms.FloatField(label="Margin of Victory", initial="0.01", max_value=1.0, min_value=0.0)
    confidence = forms.FloatField(label="Confidence level desired", initial="0.99", max_value=1.0, min_value=0.0)
    s = forms.FloatField(label="Maximum Within-Precinct-Miscount assumed", initial="0.20", max_value=1.0, min_value=0.0)
    contest_name = forms.CharField(initial="Test Contest", max_length=100)

def stats(request):
    """A form allowing the user to get selection statistics for a
    given margin, confidence, etc.  The result is returned via the
    same page.
    """

    if request.method == 'POST':
        form = StatsForm(request.POST)
        if form.is_valid():
            return render_to_response('electionaudits/stats.html', {
                    'form': form,
                    'stats': selection_stats(
                        [(500,)]*300 + [(200,)]*200 + [(40,)]*100,
                        float(form.cleaned_data['margin']),
                        form.cleaned_data['contest_name'],
                        1.0 - float(form.cleaned_data['confidence']),
                        float(form.cleaned_data['s']),
                        )
                    })
    else:
        form = StatsForm()

    return render_to_response('electionaudits/stats.html', {
        'form': form,
    })
