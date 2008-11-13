import os
import operator
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from electionaudits.models import *
import electionaudits.parsers

def report(request, contest):
    """Generate audit report for all ContestBatches and VoteCounts
    associated  with the contest"""

    contest = get_object_or_404(Contest, id=contest)

    stats = contest.stats()

    contest_batches = contest.contestbatch_set.all()

    wpm = 0.2

    audit_units = []
    for cb in contest_batches:
        cb.ssr = cb.batch.ssr()
        cb.threshhold = 1.0 - math.exp(-(cb.contest_ballots() * 2.0 * wpm) / stats['negexp_w'])
        if cb.ssr != "":
            cb.priority = cb.threshhold / cb.ssr
        else:
            cb.priority = ""
        audit_units.append(cb)

    if audit_units[0].priority != "":
        audit_units.sort(reverse=True, key=operator.attrgetter('priority'))

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
