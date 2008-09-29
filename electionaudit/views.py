from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from electionaudit.models import *

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

"""
Need some stats/invariants - who won contest, total votes, etc

load primary data.  support multiple elections....

Need a restful way to make auditable units
perhaps a form button on the auditable report to say "not for public"
or something?  and logic to provide either full report or public one.

or duplicate data totally?

def consolidate(...):

def detail(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    return render_to_response('polls/detail.html', {'poll': p})

def vote(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    try:
        selected_choice = p.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the poll voting form.
        return render_to_response('polls/detail.html', {
            'poll': p,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect('/polls/%s/results/' % p.id)

def results(request, poll_id):
    p = get_object_or_404(Poll, pk=poll_id)
    return render_to_response('polls/results.html', {'poll': p})
"""
