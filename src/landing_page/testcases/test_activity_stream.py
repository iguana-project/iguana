"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls.base import reverse
from actstream.models import following, followers, user_stream
from project.models import Project
from event import signals
from landing_page.handler import ProjectHandler
from landing_page.actstream_util import unfollow_project, follow_project


project_settings = {
    'name': 'test_project',
    'name_short': 'tp',
    'description': 'test',
}


class TestActivityStream(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('foo', 'foo@testing.com', 'foo1234')
        cls.user3 = get_user_model().objects.create_user('bar', 'bar@testing.com', 'bar1234')

    def setUp(self):
        self.client.force_login(self.user)
        # create a default project
        project_settings["manager"] = (self.user.pk)
        self.client.post(reverse('project:create'), project_settings)
        self.project = Project.objects.filter(name_short=project_settings['name_short']).first()

    def test_activity_view_and_template(self):
        # TODO TESTCASE see invite_users/testcases/test_invite_users.py as example
        pass

    def test_rediret_to_login_and_login_required(self):
        # TODO TESTCASE see invite_users/testcases/test_invite_users.py as example
        pass

    def test_follow_project(self):
        unfollow_project(self.user, self.project)
        self.assertNotIn(self.project, following(self.user))
        # follow the project with the follow button
        self.client.get(reverse('project:detail', kwargs={'project': project_settings['name_short']}) +
                        "?follow=true")
        self.assertIn(self.project, following(self.user))

    def test_unfollow_project(self):
        # unfollow the project with the unfollow button on the dashboard
        self.client.get(reverse('landing_page:home') + "?unfollow=" + str(self.project.pk))
        self.assertNotIn(self.project, following(self.user))

        # follow the project again
        follow_project(self.user, self.project)

        # unfollow the project with the unfollow button on the project page
        self.client.get(reverse('project:detail', kwargs={'project': project_settings['name_short']}) +
                        "?follow=false")
        self.assertNotIn(self.project, following(self.user))

    def test_auto_follow_on_created_project(self):
        # create a second project with the second user as developer
        project2_settings = {
            'name': 'test_project2',
            'name_short': 'tp2',
            'description': 'test2',
            'developer': (self.user2.pk),
        }
        self.client.post(reverse('project:create'), project2_settings)
        newProject = Project.objects.filter(name_short=project2_settings['name_short']).first()
        self.assertIn(self.user, followers(newProject))
        self.assertIn(self.user2, followers(newProject))

    def test_auto_follow_on_edited_project(self):
        # change the existing project by adding a new developer
        project_settings_changed = project_settings.copy()
        project_settings_changed['developer'] = (self.user2.pk)
        self.client.post(reverse('project:edit', kwargs={'project': project_settings_changed['name_short']}),
                         project_settings_changed)
        self.assertIn(self.user2, followers(self.project))

        # change the manager of the existing project
        project_settings_changed["manager"] = (self.user.pk, self.user3.pk)
        self.client.post(reverse('project:edit', kwargs={'project': project_settings_changed['name_short']}),
                         project_settings_changed)
        self.assertIn(self.user3, followers(self.project))

    def test_auto_unfollow_on_edited_project(self):
        # first change project that more users follow the project
        project_settings_changed = project_settings.copy()
        project_settings_changed['developer'] = (self.user2.pk)
        project_settings_changed["manager"] = (self.user.pk, self.user3.pk)
        self.client.post(reverse('project:edit', kwargs={'project': project_settings_changed['name_short']}),
                         project_settings_changed)

        # first remove a manager again
        project_settings_changed["manager"] = (self.user.pk)
        self.client.post(reverse('project:edit', kwargs={'project': project_settings_changed['name_short']}),
                         project_settings_changed)
        self.assertNotIn(self.user3, followers(self.project))
        self.assertIn(self.user, followers(self.project))

        # second remove a developer again
        del project_settings_changed["developer"]
        self.client.post(reverse('project:edit', kwargs={'project': project_settings_changed['name_short']}),
                         project_settings_changed)
        self.assertNotIn(self.user2, followers(self.project))

    def test_activity_stream_project(self):
        # send create event of a project
        signals.create.send(sender=Project, instance=self.project, user=self.user)
        create = user_stream(self.user).first()
        self.assertEqual(create.action_object, self.project)
        self.assertEqual(create.verb, ProjectHandler.createVerb)
        self.assertEqual(create.actor, self.user)

        # send modify event of a project
        signals.modify.send(sender=Project, instance=self.project, user=self.user, changed_data=None)
        modify = user_stream(self.user).first()
        self.assertEqual(modify.action_object, self.project)
        self.assertEqual(modify.verb, ProjectHandler.modifyVerb)
        self.assertEqual(modify.actor, self.user)

    def test_after_adjustmend_of_notification_settings(self):
        # TODO TESTCASE after adjustment on profile page for notifications for the activity stream
        pass

# TODO TESTCASE add test for every handler in handler.py
