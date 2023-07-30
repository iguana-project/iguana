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
from django.http import Http404
from django.views.generic.base import RedirectView
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _l

from slack.web.client import WebClient

from integration.models import SlackIntegration
from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from project.models import Project

try:
    from common.settings import SLACK_SECRET, SLACK_VERIFICATION, SLACK_ID, HOST
except ImportError:
    SLACK_ID = None


# TODO BUG also changing the "status" doesn't send anything
# TODO also the slack-channel should not be a private channel cuz that doesn't work either
class SlackIntegrationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SlackIntegration
    fields = ['channel', 'notify_issue_create', 'notify_issue_modify',
              'notify_comment_create', 'notify_sprint_start', 'notify_sprint_stop']
    breadcrumb = _l("Slack Integration")

    def get_success_url(self):
        return reverse('project:edit', kwargs={'project': self.kwargs['project']})

    def test_func(self):
        return get_w_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).is_manager(self.request.user)


class SlackIntegrationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SlackIntegration
    breadcrumb = _l("Delete")
    template_name = 'confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            self.get_object().delete()

        # also in case of "keep_slackintegration"
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('project:edit', kwargs={'project': self.kwargs['project']})

    def test_func(self):
        return get_w_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).is_manager(self.request.user)


# The authentication happens within this function.
# We are not able to use any Mixins here since this View is called from Slack.
class SlackIntegrationOAuthView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if not SLACK_ID:
            return reverse("project:edit", kwargs={'project': self.kwargs['project']})
        slack = WebClient("")
        code = self.request.GET['code']
        resp = slack.oauth_access(
            code=code,
            client_id=SLACK_ID,
            client_secret=SLACK_SECRET,
            redirect_uri="https://" + HOST + reverse("integration:slack:auth",
                                                     kwargs={'project': self.kwargs['project']}),
        )
        if resp['ok']:
            si = SlackIntegration()
            si.api_token = resp['access_token']
            si.project = Project.objects.get(name_short=self.kwargs['project'])
            si.save()
            return reverse("integration:slack:update", kwargs={'project': self.kwargs['project'], 'pk': si.pk})
        return reverse("project:edit", kwargs={'project': self.kwargs['project']})
