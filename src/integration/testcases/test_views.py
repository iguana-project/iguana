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
from django.test import TestCase
from django.urls import reverse

from unittest.mock import patch

from project.models import Project
from integration.models import SlackIntegration
from django.contrib.auth import get_user_model
from integration.views import SlackIntegrationOAuthView
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required, \
        user_doesnt_pass_test_and_gets_404


try:
    from common.settings import SLACK_SECRET, SLACK_VERIFICATION, SLACK_ID, HOST
except ImportError:
    SLACK_ID = None


class ViewTest(TestCase):
    short = 'proj'

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')
        cls.project = Project(creator=cls.user, name_short=cls.short)
        cls.project.save()
        cls.project.developer.set((cls.user.pk,))
        cls.project.manager.set((cls.user.pk,))
        cls.project.save()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.si = SlackIntegration(api_token="token", channel="channel")
        self.si.project = self.project
        self.si.save()

    def test_view_and_template(self):
        # TODO TESTCASE integration view and template
        #      - integration:slack:auth
        # TODO does auth even need a project?
        # view_and_template(self, SlackIntegrationOAuthView, '', 'integration:slack:auth',
        #                   address_kwargs={'project': self.project.name_short})
        #      - integration:slack:update
        # view_and_template(self, SlackIntegrationOAuthView, '', 'integration:slack:update',
        #                   address_kwargs={'pk': 1, 'project': self.project.name_short})
        # TODO needs probably more get-kwargs
        #      - integration:slack:delete
        # TODO needs probably more get-kwargs
        # view_and_template(self, SlackIntegrationOAuthView, '', 'integration:slack:delete',
        #                   address_kwargs={'pk': 1, 'project': self.project.name_short})
        pass

    def test_redirect_to_login_and_login_required(self):
        # TODO TESTCASE
        pass

    def test_user_passes_test_mixin(self):
        # non dev can neither update ...
        self.client.force_login(self.user2)
        user_doesnt_pass_test_and_gets_404(self, 'integration:slack:update',
                                           address_kwargs={'pk': 1, 'project': self.short},
                                           get_kwargs={'channel': 'foo'})

        si = SlackIntegration.objects.get(pk=self.si.pk)
        self.assertEqual(si.channel, 'channel')
        # ... nor delete the integration
        user_doesnt_pass_test_and_gets_404(self, 'integration:slack:delete',
                                           address_kwargs={'pk': 1, 'project': self.short},
                                           get_kwargs={'delete': True})

        si = SlackIntegration.objects.get(pk=self.si.pk)
        self.assertEqual(si.channel, 'channel')

        # TODO TESTCASE
        # TODO only devs are allowed to edit an integration
        # TODO how about creation of integrations?
        pass

    def test_form(self):
        response = self.client.post(
            reverse('integration:slack:update', kwargs={'pk': 1, 'project': self.short}),
            {'channel': 'foo'}
        )
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        si = SlackIntegration.objects.get(pk=self.si.pk)
        self.assertEqual(si.channel, "foo")

    def test_delete_slackintegration(self):
        response = self.client.post(reverse('integration:slack:delete', kwargs={'pk': 1, 'project': self.short}),
                                    {'delete': 'true'})
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        self.assertEqual(len(SlackIntegration.objects.all()), 0)

    def test_keep_and_dont_delete_slackintegration(self):
        response = self.client.post(reverse('integration:slack:delete', kwargs={'pk': 1, 'project': self.short}),
                                    {'keep': 'true'})
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        self.assertEqual(len(SlackIntegration.objects.all()), 1)

    @patch('integration.views.WebClient')
    def test_oauth_view_not_ok(self, slackmock):
        slackmock().oauth_access.return_value = {'ok': False}
        response = self.client.post(reverse('integration:slack:auth', kwargs={'project': self.short}) + "?code=foo")
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        slackmock.assert_called_with('')
        slackmock().oauth_access.assert_called_with(
            code="foo",
            client_id=SLACK_ID,
            client_secret=SLACK_SECRET,
            redirect_uri="https://" + HOST + reverse("integration:slack:auth", kwargs={'project': self.short}),
        )

    @patch('integration.views.WebClient')
    def test_oauth_view_ok(self, slackmock):
        slackmock().oauth_access.return_value = {'ok': True, 'access_token': "foo"}
        response = self.client.post(reverse('integration:slack:auth', kwargs={'project': self.short}) + "?code=foo")
        self.assertRedirects(response, reverse('integration:slack:update', kwargs={'pk': 2, 'project': self.short}))
        slackmock.assert_called_with('')
        slackmock().oauth_access.assert_called_with(
            code="foo",
            client_id=SLACK_ID,
            client_secret=SLACK_SECRET,
            redirect_uri="https://" + HOST + reverse("integration:slack:auth", kwargs={'project': self.short}),
        )
