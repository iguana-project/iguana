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


class ProjectGeneralAkaEditTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('a', 'b', 'c')
        project_settings['developer'] = (cls.user.pk)

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_view_and_template(self):
        # TODO TESTCASE
        # TODO your projects
        # TODO create new projects
        # TODO detail project
        # TODO edit project
        # TODO delete project
        pass

    def test_redirect_to_login_and_login_required(self):
        # TODO TESTCASE simplify this testcase verify how much of this code can be used with
        #      redirect_to_login_required() since some different status codes are used here
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

    def test_delete_project_and_affect_on_project_list(self):
        project = project_settings
        new_project = Project(name=project['name'], name_short=project['name_short'],
                              description=project['description'], creator=self.user)
        new_project.save()
        new_project.manager.add(project['developer'])
        response = self.client.get(reverse('project:list'))
        self.assertContains(response, project['name'])
        self.assertEqual(len(response.context['latest_project_list']), 1)

        # delete project
        response = self.client.post(reverse('project:delete', kwargs={'project': project['name_short']}),
                                    {'delete': 'true'})
        self.assertRedirects(response, reverse('project:list'))
        response = self.client.get(response['location'])
        self.assertTemplateUsed(response, 'project/project_list.html')
        self.assertNotContains(response, project['name'])
        self.assertEqual(len(response.context['latest_project_list']), 0)

    def test_keep_and_dont_delete_project(self):
        project = project_settings
        new_project = Project(name=project['name'], name_short=project['name_short'],
                              description=project['description'], creator=self.user)
        new_project.save()
        new_project.manager.add(project['developer'])
        response = self.client.post(reverse('project:delete', kwargs={'project': project['name_short']}),
                                    {'keep': 'true'}, follow=True)
        self.assertTemplateUsed(response, 'project/project_edit.html')
        self.assertContains(response, project['name'])

    # TODO TESTCASE - merge with new testcases below
    def test_edit(self):
        project = project_settings.copy()
        new_project = Project(name=project['name'], name_short=project['name_short'],
                              description=project['description'], creator=self.user)
        new_project.save()
        new_project.manager.add(project['developer'])

        response = self.client.get(reverse('project:edit', kwargs={'project': project['name_short']}))
        self.assertEqual(response.status_code, 200)

        project['name'] = 'renamed_project'

        response = self.client.post(reverse('project:edit', kwargs={'project': project['name_short']}),
                                    project, follow=True)
        self.assertContains(response, project['name'])

        # TODO TESTCASE
        # TODO test columns listed
        # TODO test integrations listed

    def test_name_shown(self):
        # TODO TESTCASE the project name shall be listed
        # TODO TESTCASE modify and retest
        pass

    def test_description_shown(self):
        # TODO TESTCASE the project description shall be listed
        # TODO TESTCASE modify and retest
        pass

    def test_manager_shown(self):
        # TODO TESTCASE the project manager shall be listed
        # TODO TESTCASE modify and retest
        pass

    def test_developer_shown(self):
        # TODO TESTCASE the project developer shall be listed
        # TODO TESTCASE modify and retest
        pass

    def test_columns_shown(self):
        # TODO TESTCASE the project columns shall be listed
        # TODO TESTCASE modify and retest
        pass

    def test_integrations_shown(self):
        # TODO TESTCASE the project integrations shall be listed
        # TODO TESTCASE modify and retest
        pass
