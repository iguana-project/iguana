"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
