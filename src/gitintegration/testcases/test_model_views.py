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
import os
import stat
import tempfile
from django.core.files import File

from gitintegration.views import RepositoryDetailView, RepositoryListView
from gitintegration.models import Repository
from project.models import Project
from django.contrib.auth import get_user_model

from common.settings.common import REPOSITORY_ROOT, BASE_DIR
from common.testcases.generic_testcase_helper import user_doesnt_pass_test_and_gets_404
from django.core.exceptions import ValidationError


class GitIntegrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()

    def test_path_validator(self):
        filecontent1 = 'Hello World File 1'
        tmp1 = tempfile.NamedTemporaryFile(delete=False)
        tmp1.write(filecontent1.encode())
        tmp1.close()
        filecontent2 = 'Hello World File 2'
        tmp2 = tempfile.NamedTemporaryFile(delete=False)
        tmp2.write(filecontent2.encode())
        tmp2.close()

        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                response = self.client.post(reverse('project:gitintegration:create',
                                                    kwargs={'project': self.project.name_short}
                                                    ),
                                            {'url': 'blubber-url',
                                             'rsa_priv_path': f1,
                                             'rsa_pub_path': f2,
                                             },
                                            follow=True)

        repo = Repository(project=self.project, url='')

        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                repo.rsa_priv_path = File(f1)
                repo.rsa_pub_path = File(f2)

                tests = ['',
                         'blub',
                         'bla://great.url/path',
                         'bla://../../letstestthis',
                         REPOSITORY_ROOT,
                         BASE_DIR,
                         os.path.join(REPOSITORY_ROOT, 'foreignRepo_1'),
                         os.path.join(BASE_DIR, 'dir'),
                         '/opt/repo_path'
                         ]

                for t in tests:
                    repo.url = t
                    self.assertRaises(ValidationError, repo.clean_fields)
                    try:
                        repo.clean_fields()
                    except ValidationError as e:
                        self.assertIn('url', e.message_dict.keys())

        # cleanup tmp-files
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)

    def test_add_edit_list_detail_delete_allowed_for_manager(self):
        self.project.manager.add(self.user)
        self.project.save()

        filecontent1 = 'Hello World File 1'
        tmp1 = tempfile.NamedTemporaryFile(delete=False)
        tmp1.write(filecontent1.encode())
        tmp1.close()
        filecontent2 = 'Hello World File 2'
        tmp2 = tempfile.NamedTemporaryFile(delete=False)
        tmp2.write(filecontent2.encode())
        tmp2.close()

        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                response = self.client.post(reverse('project:gitintegration:create',
                                                    kwargs={'project': self.project.name_short}
                                                    ),
                                            {'url': 'git://blubber.url',
                                             'rsa_priv_path': f1,
                                             'rsa_pub_path': f2,
                                             },
                                            follow=True)

        self.assertNotContains(response, "Your account doesn't have access to this page")
        self.project.refresh_from_db()
        self.assertEqual(self.project.repos.count(), 1)
        repo = self.project.repos.first()
        self.assertEqual(repo.url, 'git://blubber.url')
        self.assertEqual(repo.__str__(), "Repository git://blubber.url")
        self.assertIn(filecontent1, repo.rsa_priv_path.read().decode())
        self.assertIn(filecontent2, repo.rsa_pub_path.read().decode())
        # read() opened the file
        repo.rsa_priv_path.close()
        repo.rsa_pub_path.close()

        # check file permissions, we want 600
        self.assertEqual(oct(stat.S_IMODE(os.stat(repo.rsa_priv_path.path).st_mode)), '0o600')
        self.assertEqual(oct(stat.S_IMODE(os.stat(repo.rsa_pub_path.path).st_mode)), '0o600')

        # for some reason these paths gets modified during the testcase
        private_path = repo.rsa_priv_path.path
        public_path = repo.rsa_pub_path.path

        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                response = self.client.post(reverse('project:gitintegration:edit',
                                                    kwargs={'project': self.project.name_short,
                                                            'repository': '1'}
                                                    ),
                                            {'url': 'git://blubber.url',
                                             'rsa_priv_path': f2,
                                             'rsa_pub_path': f1,
                                             },
                                            follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page")
        self.project.refresh_from_db()
        self.assertEqual(self.project.repos.count(), 1)
        repo = self.project.repos.first()
        self.assertEqual(repo.url, 'git://blubber.url')
        self.assertIn(filecontent2, repo.rsa_priv_path.read().decode())
        self.assertIn(filecontent1, repo.rsa_pub_path.read().decode())
        # read() opened the file
        repo.rsa_priv_path.close()
        repo.rsa_pub_path.close()

        # check file permissions after edit, we want 600
        self.assertEqual(oct(stat.S_IMODE(os.stat(repo.rsa_priv_path.path).st_mode)), '0o600')
        self.assertEqual(oct(stat.S_IMODE(os.stat(repo.rsa_pub_path.path).st_mode)), '0o600')

        # test list view
        response = self.client.get(reverse('project:gitintegration:list',
                                           kwargs={'project': self.project.name_short}
                                           ))
        self.assertEqual(response.context_data.get('object_list').count(), 1)
        self.assertEqual(type(response.context_data.get('view')), RepositoryListView)
        self.assertNotContains(response, "Your account doesn't have access to this page")

        # test detail view
        response = self.client.get(reverse('project:gitintegration:detail',
                                           kwargs={'project': self.project.name_short,
                                                   'repository': '1'}
                                           ))
        self.assertEqual(response.context_data.get('repository'), repo)
        self.assertEqual(type(response.context_data.get('view')), RepositoryDetailView)
        self.assertNotContains(response, "Your account doesn't have access to this page")

        # test delete view
        repo.refresh_from_db()
        response = self.client.post(reverse('project:gitintegration:delete',
                                            kwargs={'project': self.project.name_short,
                                                    'repository': '1'}
                                            ),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertEqual(Repository.objects.filter(project__pk=self.project.pk,
                                                   pk=1).count(), 0)
        self.assertEqual(os.path.isfile(repo.rsa_pub_path.path), False)
        self.assertEqual(os.path.isfile(repo.rsa_priv_path.path), False)
        self.assertEqual(os.path.isdir(repo.get_local_repo_path()), False)

        # delete the key files from the server
        os.unlink(private_path)
        os.unlink(public_path)
        # delete the key files locally
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)

    def test_add_edit_delete_not_allowed_for_developer(self):
        self.project.manager.clear()
        self.project.developer.add(self.user)
        self.project.save()

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:create',
                                           address_kwargs={'project': self.project.name_short},
                                           get_kwargs={'url': 'blubber-url', 'rsa_priv_path': '', 'rsa_pub_path': ''})

        self.project.refresh_from_db()
        self.assertEqual(self.project.repos.count(), 0)

        filecontent1 = 'Hello World File 1'
        tmp1 = tempfile.NamedTemporaryFile(delete=False)
        tmp1.write(filecontent1.encode())
        tmp1.close()
        filecontent2 = 'Hello World File 2'
        tmp2 = tempfile.NamedTemporaryFile(delete=False)
        tmp2.write(filecontent2.encode())
        tmp2.close()

        repo = Repository(project=self.project, url='blub-url')

        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                repo.rsa_priv_path = File(f1)
                repo.rsa_pub_path = File(f2)
                repo.save()

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:edit',
                                           address_kwargs={'project': self.project.name_short, 'repository': '1'},
                                           get_kwargs={'url': 'blubber', 'rsa_priv_path': '', 'rsa_pub_path': '', })

        self.project.refresh_from_db()
        self.assertEqual(self.project.repos.count(), 1)
        self.assertEqual(self.project.repos.first().url, 'blub-url')

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:delete',
                                           address_kwargs={'project': self.project.name_short, 'repository': '1'},
                                           get_kwargs={'delete': 'true'})
        self.project.refresh_from_db()
        self.assertEqual(self.project.repos.count(), 1)
        self.assertEqual(self.project.repos.first().url, 'blub-url')

        # delete the key files from the server
        repo = self.project.repos.first()
        os.unlink(repo.rsa_priv_path.path)
        os.unlink(repo.rsa_pub_path.path)
        # delete the key files locally
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)

    def test_keep_and_not_delete_repository(self):
        filecontent1 = 'Hello World File 1'
        tmp1 = tempfile.NamedTemporaryFile(delete=False)
        tmp1.write(filecontent1.encode())
        tmp1.close()
        filecontent2 = 'Hello World File 2'
        tmp2 = tempfile.NamedTemporaryFile(delete=False)
        tmp2.write(filecontent2.encode())
        tmp2.close()

        repo = Repository(project=self.project, url='')
        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                repo.rsa_priv_path = File(f1)
                repo.rsa_pub_path = File(f2)
                repo.save()

        response = self.client.post(reverse('project:gitintegration:delete',
                                            kwargs={'project': self.project.name_short,
                                                    'repository': '1'}
                                            ),
                                    {'keep': 'true'},
                                    follow=True)
        self.assertEqual(self.project.repos.count(), 1)

        # delete the key files from the server
        os.unlink(repo.rsa_priv_path.path)
        os.unlink(repo.rsa_pub_path.path)
        # delete the key files locally
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)

    def test_detail_allowed_for_developer(self):
        self.project.manager.clear()
        self.project.developer.clear()
        self.project.developer.add(self.user)
        self.project.save()

        filecontent1 = 'Hello World File 1'
        tmp1 = tempfile.NamedTemporaryFile(delete=False)
        tmp1.write(filecontent1.encode())
        tmp1.close()
        filecontent2 = 'Hello World File 2'
        tmp2 = tempfile.NamedTemporaryFile(delete=False)
        tmp2.write(filecontent2.encode())
        tmp2.close()

        repo = Repository(project=self.project, url='blub-url')

        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                repo.rsa_priv_path = File(f1)
                repo.rsa_pub_path = File(f2)
                repo.save()

        response = self.client.get(reverse('project:gitintegration:detail',
                                           kwargs={'project': self.project.name_short,
                                                   'repository': '1'}
                                           ),
                                   follow=True)
        self.assertEqual(response.context_data.get('repository'), repo)
        self.assertEqual(type(response.context_data.get('view')), RepositoryDetailView)
        self.assertNotContains(response, "Your account doesn't have access to this page")
        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                self.assertContains(response, str(f2.read()))
                self.assertNotContains(response, str(f1.read()))

        # delete the key files from the server
        os.unlink(repo.rsa_priv_path.path)
        os.unlink(repo.rsa_pub_path.path)
        # delete the key files locally
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)

    def test_views_not_allowed_for_non_project_member(self):
        filecontent1 = 'Hello World File 1'
        tmp1 = tempfile.NamedTemporaryFile(delete=False)
        tmp1.write(filecontent1.encode())
        tmp1.close()
        filecontent2 = 'Hello World File 2'
        tmp2 = tempfile.NamedTemporaryFile(delete=False)
        tmp2.write(filecontent2.encode())
        tmp2.close()

        repo = Repository(project=self.project, url='blub-url')
        with open(tmp1.name, 'r') as f1:
            with open(tmp2.name, 'r') as f2:
                repo.rsa_priv_path = File(f1)
                repo.rsa_pub_path = File(f2)
                repo.save()

        response = self.client.get(reverse('project:gitintegration:list',
                                           kwargs={'project': self.project.name_short}
                                           ),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:detail',
                                           address_kwargs={'project': self.project.name_short, 'repository': repo.pk})

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:create',
                                           address_kwargs={'project': self.project.name_short},
                                           get_kwargs={'url': 'blubber', 'rsa_priv_path': '', 'rsa_pub_path': ''})

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:edit',
                                           address_kwargs={'project': self.project.name_short, 'repository': repo.pk},
                                           get_kwargs={'url': 'blubber', 'rsa_priv_path': '', 'rsa_pub_path': ''})

        user_doesnt_pass_test_and_gets_404(self, 'project:gitintegration:delete',
                                           address_kwargs={'project': self.project.name_short, 'repository': repo.pk},
                                           get_kwargs={'delete': 'true'})

        # delete the key files from the server
        os.unlink(repo.rsa_priv_path.path)
        os.unlink(repo.rsa_pub_path.path)
        # delete the key files locally
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)
