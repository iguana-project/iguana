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
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.project = Project(creator=cls.user, name_short='PRJ')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

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
