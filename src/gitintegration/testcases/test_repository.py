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

from gitintegration.views import RepositoryDetailView, RepositoryListView, RepositoryCreateView,\
                                 RepositoryEditView, RepositoryDeleteView
from gitintegration.models import Repository, Commit
from gitintegration.frontend import Frontend
from search.frontend import SearchFrontend
from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model
from common.celery import import_commits
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class GitFrontendTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.project = Project(creator=cls.user, name_short='PRJ')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some of those tests, so they should NOT be created in setUpTestData()

    def test_view_and_template(self):
        # TOOD TESTCASE FIX THESE
        #      - RepositoryListView - list
        # TODO need to create some repositories first
        # view_and_template(self, RepositoryListView, 'repository/repository_list.html', 'project:gitintegration:list',
        #                   address_kwargs={'project': self.project.name_short})
        #      - RepositoryCreateView - create
        # view_and_template(self, RepositoryCreateView, 'repository/repository_create.html',
        #                  'project:gitintegration:create',
        #                   address_kwargs={'project': self.project.name_short})
        #      - RepositoryDetailView - detail
        # view_and_template(self, RepositoryDetailView, 'repository/repository_detail.html',
        #                   'project:gitintegration:detail',
        #                    address_kwargs={'project': self.project.name_short, project:gitintegration: 'TODO')
        #      - RepositoryEditView - edit
        # view_and_template(self, RepositoryEditView, 'repository/repository_edit.html', 'project:gitintegration:edit',
        #                   address_kwargs={'project': self.project.name_short, project:gitintegration: 'TODO')
        #      - RepositoryDeleteView - delete
        # view_and_template(self, RepositoryDeleteView, 'repository/repository_delete.html',
        #                   'project:gitintegration:delete',
        #                    address_kwargs={'project': self.project.name_short, project:gitintegration: 'TODO')
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - RepositoryListView - list
        #      - RepositoryCreateView - create
        #      - RepositoryDetailView - detail
        #      - RepositoryEditView - edit
        #      - RepositoryDeleteView - delete
        #      - ...
        pass

    def test_functionality(self):
        # TODO TESTCASE implement some testcases
        pass
