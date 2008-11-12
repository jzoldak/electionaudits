import os
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from electionaudits.models import *
import electionaudits.parsers

"""
display calc for "overall margin"
{%if proportion is 100%, use margin
else if missing, say <strong>MISSING</strong>
else
 {{ object.overall_margin|floatformat:3 }}%
"""

def report(request, contest):
    # Look up the contest (and raise a 404 if it can't be found).
    try:
        contest = Contest.objects.get(name__iexact=contest)
    except Contest.DoesNotExist:
        raise Http404

    #assert False, VoteCount.objects.filter(contest=contest)

    # Use the object_list view for the heavy lifting.
    return list_detail.object_list(
        request,
        queryset = VoteCount.objects.filter(contest=contest),
        template_name = "report.html",
        template_object_name = "votecounts",
        extra_context = {"contest" : contest}
    )

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
