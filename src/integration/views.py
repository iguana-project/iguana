"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
        try:
            get_w_object_or_404(self.request.user, Project,
                                name_short=self.kwargs.get('project'))
        except Http404:
            return 0
        return 1


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
        try:
            get_w_object_or_404(self.request.user, Project,
                                name_short=self.kwargs.get('project'))
        except Http404:
            return 0
        return 1


# The authentication happens within this function.
# We are not able to use any Mixins here since this View is called from Slack.
class SlackIntegrationOAuthView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if not SLACK_ID:
            return reverse("project:edit", kwargs={'project': self.kwargs['project']})
        slack = WebClient("")
        code = self.request.GET['code']
        resp = slack.api_call(
            "oauth.access",
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
