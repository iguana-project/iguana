"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.urls import reverse

from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model

project_settings = {
    'name': 'test_project',
    'name_short': 'tp',
    'description': 'test',
}


class ProjectUniversalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('a', 'b', 'c')
        project_settings['developer'] = (cls.user.pk)

    def setUp(self):
        self.client.force_login(self.user)

    def test_view_and_template(self):
        # TODO TESTCASE
        # TODO your projects
        # TODO create new projects
        # TODO detail project
        # TODO edit project
        # TODO delete project
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.force_login(self.user2)

        project = Project(creator=self.user, name_short='PRJ')
        project.save()
        project.developer.add(self.user2)

        # try to delete as developer => should fail
        response = self.client.post(reverse('project:delete', kwargs={'project': 'PRJ'}),
                                    {'delete': 'true'}, follow=True)
        self.assertContains(response, "Your account doesn't have access to this page")
        self.assertEqual(Project.objects.filter(name_short='PRJ').count(), 1)

        # try to leave as non-member
        project.developer.clear()
        response = self.client.post(reverse('project:leave', kwargs={'project': 'PRJ'}),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your account doesn't have access to this page")

        # detail view only accessible for members
        response = self.client.post(reverse('project:detail', kwargs={'project': 'PRJ'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your account doesn't have access to this page")

        # usertimelog not accessible for non-members
        # NOTE dispatch() is called before test_func(), so we receive 404 here
        response = self.client.post(reverse('project:usertimelog',
                                            kwargs={'project': 'PRJ', 'username': 'a'}
                                            ),
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # timelog not accessible for non-members
        # NOTE dispatch() is called before test_func(), so we receive 404 here
        response = self.client.post(reverse('project:timelog',
                                            kwargs={'project': 'PRJ'}
                                            ),
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # add user2 as manager and try delete -> keep => no deletion
        project.manager.add(self.user2)
        response = self.client.post(reverse('project:delete', kwargs={'project': 'PRJ'}),
                                    {'keep': 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Your account doesn't have access to this page")
        self.assertEqual(Project.objects.filter(name_short='PRJ').count(), 1)

        # try leave -> keep
        response = self.client.post(reverse('project:leave', kwargs={'project': 'PRJ'}),
                                    {'keep': 'true'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Your account doesn't have access to this page")
        project.refresh_from_db()
        self.assertEqual(project.manager.count(), 1)

        self.client.force_login(self.user)

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        # TODO your projects
        # TODO detail project
        # TODO edit project (only manager)
        # TODO delete view (only manager)
        # TODO s.a. def test_create_project_change_project_manager(self):
        pass

    def test_project_management_with_get_requests_disabled(self):
        # TODO TESTCASE
        # TODO your projects
        # TODO create new projects
        # TODO detail project
        # TODO edit project
        # TODO delete project
        pass

    # TODO can be removed as soon as test_user_passes_test_mixin() is done
    def test_create_project_change_project_manager(self):
        user2 = get_user_model().objects.create_user('test2', 'test2@testing.com', 'test1234')
        project = project_settings.copy()
        project['developer'] = (self.user.pk, user2.pk)
        response = self.client.post(reverse('project:create'), project)
        self.assertRedirects(response, reverse('project:detail', kwargs={'project': project['name_short']}))

        project['manager'] = (user2.pk)
        response = self.client.post(reverse('project:edit', kwargs={'project': project['name_short']}), project)
        response = self.client.get(reverse('project:edit', kwargs={'project': project['name_short']}))
        self.assertEqual(response.status_code, 302)  # logged in user isn't manager anymore

        self.client.logout()
        self.client.force_login(user2)
        response = self.client.get(reverse('project:edit', kwargs={'project': project['name_short']}))
        self.assertEqual(response.status_code, 200)  # new manager gets the edit page

    def test_create_and_affect_on_project_list(self):
        project = project_settings

        response = self.client.post(reverse('project:create'), project)
        response = self.client.get(reverse('project:list'))
        self.assertContains(response, project['name'])
        self.assertEqual(len(response.context['latest_project_list']), 1)

        project = {
            'name': 'test_projekt2',
            'name_short': 'tp2',
            'description': 'test2',
            'developer': (self.user.pk)
        }
        response = self.client.post(reverse('project:create'), project, Follow=True)
        response = self.client.get(reverse('project:list'))
        self.assertEqual(len(response.context['latest_project_list']), 2)

    def test_leave_project(self):
        new_project = Project(name='asdf', name_short='asd', creator=self.user)
        new_project.save()
        new_project.manager.add(self.user)
        user2 = get_user_model().objects.create_user('test2', 'test@testing2.com', 'test1234')
        response = self.client.post(reverse('project:leave', kwargs={'project': 'asd'}),
                                    {'delete': ''},
                                    follow=True)
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': 'asd'}))
        self.assertContains(response, 'last manager')
        new_project.developer.add(user2)
        response = self.client.post(reverse('project:leave', kwargs={'project': 'asd'}),
                                    {'delete': ''},
                                    follow=True)
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': 'asd'}))
        self.assertContains(response, 'last manager')
        new_project.manager.add(user2)
        response = self.client.post(reverse('project:leave', kwargs={'project': 'asd'}),
                                    {'delete': ''},
                                    follow=True)
        self.assertRedirects(response, reverse('project:list'))
        self.assertNotIn(self.user, new_project.get_members())
