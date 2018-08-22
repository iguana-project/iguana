"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect

from datetime import timedelta
import pytz

from lib.custom_model import get_r_object_or_404
from .forms import TimelogCreateForm, TimelogEditForm, TimelogCreateForm2
from issue.models import Issue
from project.models import Project
from .models import Timelog, Punch
from .templatetags.filter import duration
# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


# routing is in issue
# TODO log with: current date = current date and time > 0 results in successful log - does this make sense?
# TODO same for start date is in the past but the logged time is greater than the delta(start, now)
#      both cases means: Stopdate > now
class TimelogCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Timelog
    template_name = 'timelog/timelog_create.html'
    form_class = TimelogCreateForm
    breadcrumb = _l("Log time")

    def get_success_url(self):
        issue = Issue.objects.get(project__name_short=self.kwargs.get('project'), number=self.kwargs.get('sqn_i'))
        return reverse('issue:detail', kwargs={"project": issue.project.name_short, "sqn_i": issue.number})

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.issue = Issue.objects.get(project__name_short=self.kwargs.get('project'),
                                                number=self.kwargs.get('sqn_i')
                                                )
        return super(TimelogCreateView, self).form_valid(form)

    def test_func(self):
        try:
            get_r_object_or_404(self.request.user, Project,
                                name_short=self.kwargs.get('project')).developer_allowed(self.request.user)
        except Http404:
            return 0
        return 1


class TimelogEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Timelog
    template_name = 'timelog/timelog_edit.html'
    form_class = TimelogEditForm
    breadcrumb = _l("Edit Log")

    def post(self, request, *args, **kwargs):
        if 'save_timelog_change' in request.POST:
            return super(UpdateView, self).post(self, request, args, kwargs)
        # direct to delete-template
        return HttpResponseRedirect(reverse('issue:logdelete', kwargs={'project': self.kwargs['project'],
                                    'sqn_i': self.kwargs['sqn_i'], 'sqn_l': self.kwargs['sqn_l']}))

    def get_object(self):
        return get_r_object_or_404(self.request.user, Timelog, issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'), number=self.kwargs.get('sqn_l'))

    def get_success_url(self):
        next_url = self.request.GET.get('next', '')
        if next_url == '':
            return reverse('timelog:loginfo')
        else:
            return next_url

    def test_func(self):
        try:
            self.get_object().edit_allowed(self.request.user)
        except Exception:
            return 0
        return 1


# shows all logs for all projects + issues for the own user
class TimelogLoginfoPerUserView(LoginRequiredMixin, CreateView):
    model = Timelog
    template_name = 'timelog/timelog_list_peruser.html'
    form_class = TimelogCreateForm2
    hide_breadcrumbs = True

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs(), user=self.request.user)
        return form

    def get_success_url(self):
        return reverse('timelog:loginfo')

    def get_context_data(self, **kwargs):
        context = super(TimelogLoginfoPerUserView, self).get_context_data(**kwargs)
        context['logs'] = Timelog.objects.filter(user=self.request.user).order_by('-created_at')[:10]
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.add_message(self.request, messages.SUCCESS,
                             _('You successfully logged Time on')+' '+form.instance.issue.title
                             )
        return super(TimelogLoginfoPerUserView, self).form_valid(form)


class TimelogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Timelog
    hide_breadcrumbs = True
    template_name = 'confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            self.get_object().delete()
            return HttpResponseRedirect(self.get_success_url())
        # in case of "keep_timelog" we redirect to the per-user-timelog-list even if a next-parameter is provided
        return HttpResponseRedirect(reverse('timelog:loginfo'))

    def get_object(self):
        return get_r_object_or_404(self.request.user, Timelog, issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'), number=self.kwargs.get('sqn_l'))

    def get_success_url(self):
        next_url = self.request.GET.get('next', '')
        if next_url == '':
            return reverse('timelog:loginfo')
        else:
            return next_url

    def test_func(self):
        return self.get_object().edit_allowed(self.request.user)


class TimelogGetActivityDataView(LoginRequiredMixin, TemplateView):
    template_name = 'timelog/timelog_activity.html'
    hide_breadcrumbs = True


class TimelogD3View(LoginRequiredMixin, TemplateView):
    template_name = 'timelog/timelog_d3.html'
    hide_breadcrumbs = True


class TimelogArchivView(LoginRequiredMixin, TemplateView):
    template_name = 'timelog/timelog_archiv.html'
    hide_breadcrumbs = True

    def get_context_data(self, **kwargs):
        context = super(TimelogArchivView, self).get_context_data(**kwargs)
        log_list = Timelog.objects.filter(user=self.request.user).order_by('-created_at')
        paginator = Paginator(log_list, 10)
        page = self.request.GET.get('page')
        try:
            logs = paginator.page(page)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            logs = paginator.page(paginator.num_pages)
        context['logs'] = logs
        return context


class PunchView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('sprint:sprintboard', kwargs={'project': self.kwargs.get('project')})

    def post(self, request, *args, **kwargs):
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=self.kwargs.get('project'),
                                    number=self.kwargs.get('sqn_i')
                                    )
        user = request.user
        punch = Punch.objects.filter(user=user)
        if punch.exists() and int(self.kwargs.get('sqn_i')) == punch.first().issue.number:
            punch = punch.first()
            time = timezone.now()-punch.created_at
            sec = time.total_seconds()
            if sec < 60:
                sec = 60
            else:
                sec = sec - (sec % 60)
            time = timedelta(seconds=sec)
            log = Timelog(user=user, issue=issue, created_at=punch.created_at, time=time)
            log.save()
            punch.delete()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Punched out') + (': ') + _('Successfully logged ') +
                                 duration(log.time) + _(' on ') + issue.get_ticket_identifier(),
                                 )
        elif punch.exists() and self.kwargs.get('sqn_i') != punch.first().issue.number:
            punch = Punch.objects.filter(user=user).first()
            messages.add_message(request,
                                 messages.ERROR,
                                 _("You can't work on different Issues at the same time.") +
                                 _("Please first finish your work on ") +
                                 punch.issue.get_ticket_identifier(),
                                 )
        else:
            punch = Punch(user=user, issue=issue)
            punch.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Punched in on ') + issue.get_ticket_identifier() + '. The clock is ticking.',
                                 )

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def test_func(self):
        try:
            get_r_object_or_404(self.request.user, Project,
                                name_short=self.kwargs.get('project')).developer_allowed(self.request.user)
        except Http404:
            return 0
        return 1
