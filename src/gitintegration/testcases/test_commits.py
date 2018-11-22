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
import tempfile
import shutil
import json

from git import Repo, Git

from gitintegration.views import RepositoryDetailView
from gitintegration.models import Repository, Commit
from gitintegration.frontend import Frontend
from search.frontend import SearchFrontend
from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model
from common.celery import import_commits


class GitFrontendTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: this element gets modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()

        self.issue = Issue(title="Test-Issue",
                           project=self.project,
                           kanbancol=self.project.kanbancol.first(),
                           type="Bug")
        self.issue.save()

    def test_clone_and_import(self):
        repo_path = '/tmp/gitpythonrepo'

        self.project.manager.add(self.user)
        self.project.developer.add(self.user2)
        self.project.save()

        filecontent1 = 'Hello World File 1'
        temp1 = tempfile.NamedTemporaryFile(delete=False)
        temp1.write(filecontent1.encode())
        temp1.close()
        filecontent2 = 'Hello World File 2'
        temp2 = tempfile.NamedTemporaryFile(delete=False)
        temp2.write(filecontent2.encode())
        temp2.close()

        with open(temp1.name, 'r') as f1:
            with open(temp2.name, 'r') as f2:
                response = self.client.post(reverse('project:gitintegration:create',
                                                    kwargs={'project': self.project.name_short}
                                                    ),
                                            {'url': 'http://im-a-dum.my/repo/path',
                                             'rsa_priv_path': f1,
                                             'rsa_pub_path': f2,
                                             },
                                            follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page")
        self.project.refresh_from_db()
        self.assertEqual(self.project.repos.count(), 1)
        repo = self.project.repos.first()
        self.assertEqual(repo.url, 'http://im-a-dum.my/repo/path')

        # set correct repo path. This is not possible via request due to validators
        repo.url = repo_path
        repo.save()

        self.assertEqual(repo.url, repo_path)
        self.assertIn(filecontent1, repo.rsa_priv_path.read().decode())
        self.assertIn(filecontent2, repo.rsa_pub_path.read().decode())

        # try importing without valid remote repository
        shutil.rmtree(repo_path, ignore_errors=True)
        shutil.rmtree(repo.get_local_repo_path(), ignore_errors=True)
        import_commits()
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, False)

        # create a local repo
        initial_file = repo_path + '/initial'
        remote_repo = Repo.init(repo_path)
        f_open = open(initial_file, 'wb')
        f_open.write('Content in first file\n'.encode())
        f_open.close()
        remote_repo.index.add([initial_file])
        remote_repo_master = remote_repo.index.commit("initial commit")
        initial_sha = remote_repo_master.hexsha

        # try import again, connection should now work, but no commit to import
        Frontend.import_new_commits(repo)
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(repo.last_commit_processed, remote_repo_master.hexsha)
        self.assertEqual(Commit.objects.count(), 0)

        # create commit with issue identifier in message
        f = repo_path + '/file1'
        open(f, 'wb').close()
        remote_repo.index.add([f])
        remote_repo_master = remote_repo.index.commit(self.project.name_short + "-1 commit body")

        # import again, self.issue should now have a commit associated, activity shoud have increased
        activity = len(json.loads(repo.project.activity))
        Frontend.import_new_commits(repo)
        repo.refresh_from_db()
        self.assertGreater(len(json.loads(repo.project.activity)), activity)
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(repo.last_commit_processed, remote_repo_master.hexsha)
        self.assertEqual(Commit.objects.count(), 1)
        self.assertEqual(self.issue.commits.count(), 1)

        # examine commit
        c = self.issue.commits.first()
        self.assertNotEqual(c.author, '')
        self.assertEqual(c.name, remote_repo_master.hexsha)
        self.assertEqual(c.repository, repo)
        self.assertEqual(c.message, "commit body")
        self.assertEqual(len(c.get_tags()), 0)
        firstchange = c.get_changes()['file1']
        self.assertEqual(firstchange['lines'], 0)
        self.assertEqual(firstchange['insertions'], 0)
        self.assertEqual(firstchange['deletions'], 0)

        # empty changes, get_changes() must not crash
        savedchanges = c.get_changes()
        c.changes = ""
        c.save()
        c.get_changes()
        c.set_changes(savedchanges)
        self.assertEqual(c.get_changes(), remote_repo_master.stats.files)

        # permissions checks maps to project's functions
        self.assertEqual(c.user_has_read_permissions(self.user), True)
        self.assertEqual(c.user_has_read_permissions(self.user2), True)
        self.assertEqual(c.user_has_write_permissions(self.user), True)
        self.assertEqual(c.user_has_write_permissions(self.user2), False)

        # reset last_commit_processed and try again: no duplicates should appear in Commits
        repo.last_commit_processed = ''
        repo.save()
        Frontend.import_new_commits(repo)
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(repo.last_commit_processed, remote_repo_master.hexsha)
        self.assertEqual(Commit.objects.count(), 1)
        self.assertEqual(self.issue.commits.count(), 1)

        # commit with invalid issue id
        f = repo_path + '/file2'
        open(f, 'wb').close()
        remote_repo.index.add([f])
        remote_repo_master = remote_repo.index.commit(self.project.name_short + "-42 commit body with invalid issue id")
        # activity should not change
        activity = len(json.loads(repo.project.activity))
        Frontend.import_new_commits(repo)
        repo.refresh_from_db()
        self.assertEqual(len(json.loads(repo.project.activity)), activity)
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(repo.last_commit_processed, remote_repo_master.hexsha)
        self.assertEqual(Commit.objects.count(), 1)
        self.assertEqual(self.issue.commits.count(), 1)

        # create commit with issue identifier in message
        f = repo_path + '/file3'
        f_open = open(f, 'wb')
        f_open.write('Fancy file content\nEven with newline\n'.encode())
        f_open.close()
        remote_repo.index.add([f])
        remote_repo_master = remote_repo.index.commit(self.project.name_short + "-1 commit body for file 3\n" +
                                                      "This time with longer commit message")
        tag = remote_repo.create_tag('Test-Tag', ref=remote_repo_master)

        # import again, self.issue should now have 2 commits associated
        activity = len(json.loads(repo.project.activity))
        Frontend.import_new_commits(repo)
        repo.refresh_from_db()
        self.assertGreater(len(json.loads(repo.project.activity)), activity)
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(repo.last_commit_processed, remote_repo_master.hexsha)
        self.assertEqual(Commit.objects.count(), 2)
        self.assertEqual(self.issue.commits.count(), 2)

        # examine newest commit
        c = self.issue.commits.get(name=remote_repo_master.hexsha)
        self.assertNotEqual(c.author, '')
        self.assertEqual(c.name, remote_repo_master.hexsha)
        self.assertEqual(c.repository, repo)
        self.assertEqual(c.message, "commit body for file 3\nThis time with longer commit message")
        self.assertEqual(c.get_title(), "commit body for file 3")
        self.assertEqual(c.get_name_short(), remote_repo_master.hexsha[:7])
        firstchange = c.get_changes()['file3']
        self.assertEqual(firstchange['lines'], 2)
        self.assertEqual(firstchange['insertions'], 2)
        self.assertEqual(firstchange['deletions'], 0)
        self.assertEqual(c.__str__(), "Commit " + remote_repo_master.hexsha)
        self.assertEqual(len(c.get_tags()), 1)
        self.assertEqual(c.get_tags()[0], 'Test-Tag')

        # test file diff view
        diff = '@@ -0,0 +1,2 @@\n+Fancy file content\n+Even with newline\n'.splitlines()
        response = self.client.post(reverse('issue:commit_diff',
                                            kwargs={'project': self.project.name_short,
                                                    'sqn_i': c.issue.number,
                                                    }
                                            ),
                                    {'filename': list(c.get_changes().keys())[0],
                                     'repository': repo.pk,
                                     'commit_sha': c.get_name_short(),
                                     },
                                    )
        self.assertNotContains(response, "Your account doesn't have access to this page")
        self.assertEqual(response.context_data['diff'], diff)
        self.assertEqual(response.context_data['filename'], list(c.get_changes().keys())[0])
        self.assertEqual(response.context_data['commit_sha'], c.get_name_short())

        # add another tag to an already imported commit
        tag = remote_repo.create_tag('Another_tag', ref=remote_repo_master)
        activity = len(json.loads(repo.project.activity))
        Frontend.import_new_commits(repo)
        repo.refresh_from_db()
        self.assertGreater(len(json.loads(repo.project.activity)), activity)

        c = self.issue.commits.get(name=remote_repo_master.hexsha)
        self.assertEqual(len(c.get_tags()), 2)
        self.assertIn('Test-Tag', c.get_tags())
        self.assertIn('Another_tag', c.get_tags())

        # check with insufficient privileges
        self.project.manager.clear()
        response = self.client.post(reverse('issue:commit_diff',
                                            kwargs={'project': self.project.name_short,
                                                    'sqn_i': c.issue.number,
                                                    }
                                            ),
                                    {'filename': list(c.get_changes().keys())[0],
                                     'repository': repo.pk,
                                     'commit_sha': c.get_name_short(),
                                     },
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your account doesn't have access to this page")
        self.project.manager.add(self.user)

        # post broken data to view
        response = self.client.post(reverse('issue:commit_diff',
                                            kwargs={'project': self.project.name_short,
                                                    'sqn_i': c.issue.number,
                                                    }
                                            ),
                                    {'filename': 'blabla',
                                     'repository': repo.pk,
                                     'commit_sha': 'blubber',
                                     },
                                    follow=True)
        self.assertEqual(response.context_data['diff'], ''.splitlines())
        self.assertEqual(response.context_data['filename'], 'blabla')
        self.assertEqual(response.context_data['commit_sha'], 'blubber')

        # check that commits are searchable
        sr = SearchFrontend.query('commit body', self.user)
        self.assertEqual(len(sr), 2)
        sr = SearchFrontend.query('Commit.message ~ "commit message"', self.user)
        self.assertEqual(len(sr), 1)
        self.assertEqual(sr[0][0], "(" + c.get_name_short() + ") commit body for file 3")

        # examine file diffs
        f = repo_path + '/file4'
        f_open = open(f, 'wb')
        f_open.write('Fancy file content\n'.encode())
        f_open.close()
        remote_repo.index.add([f])
        remote_repo_master = remote_repo.index.commit('file4')
        Frontend.import_new_commits(repo)

        diff = Frontend.get_diff(repo, remote_repo_master.hexsha, 'file4')
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(diff, "@@ -0,0 +1 @@\n+Fancy file content\n")

        # check that commit changes are searchable
        sr = SearchFrontend.query('file', self.user)
        self.assertEqual(len(sr), 1)

        # check with first commit
        diff = Frontend.get_diff(repo, initial_sha, 'initial')
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, True)
        # TODO TESTCASE we're currently expecting an empty result because gitpython is broken as fuck
        self.assertEqual(diff, "")
        # self.assertEqual(diff, "@@ -0,0 +1 @@\n+Content in first file\n")

        # try with invalid filename
        diff = Frontend.get_diff(repo, c.get_name_short(), 'invalid')
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(diff, "")

        # try with invalid commit sha
        diff = Frontend.get_diff(repo, '1234567', 'invalid')
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, True)
        self.assertEqual(diff, "")

        # try with broken repo path (not yet checked out
        prj_name_short = self.project.name_short
        self.project.name_short = 'AAA'
        self.project.save()
        diff = Frontend.get_diff(repo, initial_sha, 'initial')
        repo.refresh_from_db()
        self.assertEqual(repo.conn_ok, False)
        self.assertEqual(diff, "")
        self.project.name_short = prj_name_short
        self.project.save()

        # delete the key files from the server
        os.unlink(repo.rsa_priv_path.path)
        os.unlink(repo.rsa_pub_path.path)
        # delete the key files locally
        os.unlink(temp1.name)
        os.unlink(temp2.name)
        # clean up locally
        shutil.rmtree(repo_path, ignore_errors=True)
        shutil.rmtree(repo.get_local_repo_path(), ignore_errors=True)
