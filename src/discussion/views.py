"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic.base import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.translation import ugettext as _, ugettext_lazy as _l
from django.urls import reverse
from django.shortcuts import redirect

from discussion.models import Notification
from lib.custom_model import get_r_object_or_404
from project.models import Project
from issue.models import Issue


class DiscussionsView(LoginRequiredMixin, TemplateView):
    template_name = 'discussions.html'
    hide_breadcrumbs = True

    def get_context_data(self, **kwargs):
        context = super(DiscussionsView, self).get_context_data(**kwargs)
        projects = self.request.user.get_projects()
        notifications = {}
        for project in projects:
            nots = self.request.user.notifications.filter(issue__project=project)
            if nots:
                notifications[project] = nots
        context['notifications'] = notifications
        return context


class MuteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:detail', kwargs={'project': self.kwargs['project'], 'sqn_i': self.kwargs['sqn_i']})

    def post(self, request, *args, **kwargs):
        user = self.request.user
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=self.kwargs['project'],
                                    number=self.kwargs['sqn_i'],
                                    )
        issue.participant.remove(user)
        return redirect(self.get_success_url())

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).developer_allowed(self.request.user)


class FollowView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:detail', kwargs={'project': self.kwargs['project'], 'sqn_i': self.kwargs['sqn_i']})

    def post(self, request, *args, **kwargs):
        user = self.request.user
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=self.kwargs['project'],
                                    number=self.kwargs['sqn_i'],
                                    )
        issue.participant.add(user)
        return redirect(self.get_success_url())

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).developer_allowed(self.request.user)


class SeenView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        return reverse('discussion:list')

    def post(self, *args, **kwargs):
        project_name = self.kwargs['project']
        issue_number = self.request.POST['issue']
        if int(issue_number) < 0:
            notifications = self.request.user.notifications.filter(issue__project__name_short=project_name)
        else:
            issue = get_r_object_or_404(self.request.user, Issue, project__name_short=project_name, number=issue_number)
            notifications = self.request.user.notifications.filter(issue=issue)
        for notification in notifications.all():
            notifications.delete()
        return redirect(self.get_success_url())

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).developer_allowed(self.request.user)
