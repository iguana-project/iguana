"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from django.urls import reverse
from selenium.webdriver.common.keys import Keys

import shutil
import os
from git import Repo, Git

from common.settings.common import REPOSITORY_ROOT

from project.models import Project
from issue.models import Issue
from gitintegration.models import Repository
from gitintegration.frontend import Frontend
from django.contrib.auth import get_user_model
from time import sleep


class GitIntegrationTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.user2 = get_user_model().objects.create_user('d', 'e', 'f')
        self.project = Project(creator=self.user, name="Selenium-Project", name_short="SLN")
        self.project.save()
        self.project.developer.add(self.user)
        self.project.developer.add(self.user2)
        self.project.manager.add(self.user)

        self.issue = Issue(title="Test-Issue",
                           project=self.project,
                           kanbancol=self.project.kanbancol.first(),
                           type="Bug")
        self.issue.save()

        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_gitlifecycle(self):
        driver = self.selenium
        driver.get('{}{}'.format(self.live_server_url,
                                 reverse('project:detail', kwargs={'project': self.project.name_short})))

        # create test repository
        repo_path = '/tmp/gitpythonrepo'
        shutil.rmtree(os.path.join(REPOSITORY_ROOT, 'repository_SLN_1'), ignore_errors=True)
        shutil.rmtree(repo_path, ignore_errors=True)
        remote_repo = Repo.init(repo_path)

        # init repo
        filepath = repo_path + '/README'
        f = open(filepath, 'wb')
        f.write("README content\n".encode())
        f.close()
        remote_repo.index.add([filepath])
        remote_repo_master = remote_repo.index.commit("initial commit")

        # add file to first commit
        filepath = repo_path + '/testfile1'
        f = open(filepath, 'wb')
        f.write("Testcontent\n".encode())
        f.close()
        remote_repo.index.add([filepath])
        remote_repo_master = remote_repo.index.commit("SLN-1 initial commit")

        driver.find_element_by_id("project_edit").click()
        driver.find_element_by_link_text("Repositories").click()
        driver.find_element_by_css_selector("span.glyphicon.glyphicon-plus").click()
        driver.find_element_by_id("id_url").clear()
        driver.find_element_by_id("id_url").send_keys('https://dummy-re.po/path')
        driver.find_element_by_id("id_rsa_priv_path").clear()
        driver.find_element_by_id("id_rsa_priv_path").send_keys(filepath)
        driver.find_element_by_id("id_rsa_pub_path").clear()
        driver.find_element_by_id("id_rsa_pub_path").send_keys(filepath)
        driver.find_element_by_id("id_submit_create").click()

        # set correct repo path
        repo_from_db = Repository.objects.first()
        repo_from_db.url = repo_path
        repo_from_db.save()

        driver.find_element_by_id("project_edit").click()
        driver.find_element_by_link_text("Repositories").click()
        self.assertEqual("Repository " + repo_path, driver.find_element_by_id("repo_name_1").text)
        driver.find_element_by_id("edit_repo_1").click()
        driver.find_element_by_id("id_submit_edit").click()
        driver.find_element_by_id("project_edit").click()
        driver.find_element_by_link_text("Repositories").click()
        driver.find_element_by_link_text("Repository " + repo_path).click()
        self.assertEqual("0", driver.find_element_by_id("repo_state").text)

        # import repo
        repo = self.project.repos.first()
        Frontend.import_new_commits(repo)

        driver.find_element_by_link_text("SLN").click()
        driver.find_element_by_link_text("SLN-1").click()
        self.assertEqual("(" + remote_repo_master.hexsha[:7] + ") initial commit",
                         driver.find_element_by_id("commit_1").text)

        # open the commit overview
        driver.find_element_by_id("commit_1").click()
        # wait for the fade-in animation to finish
        sleep(2)

        self.assertEqual("initial commit (" + remote_repo_master.hexsha[:7] + ")",
                         driver.find_element_by_id("title_commit_1").text)
        self.assertEqual("testfile1", driver.find_element_by_css_selector("td").text)
        self.assertEqual("1", driver.find_element_by_css_selector("span.label.label-success").text)
        self.assertEqual("0", driver.find_element_by_css_selector("span.label.label-danger").text)
        driver.find_element_by_id("diff_btn_1").click()
        self.assertIn('<div data-value="@@ -0,0 +1 @@"></div>', driver.page_source)
        self.assertIn('<div data-value="+Testcontent"></div>', driver.page_source)
        driver.get('{}{}'.format(self.live_server_url,
                                 reverse('project:detail', kwargs={'project': self.project.name_short})))
        driver.find_element_by_id("project_edit").click()
        driver.find_element_by_link_text("Repositories").click()
        driver.find_element_by_link_text("Repository " + repo_path).click()
        self.assertEqual("", driver.find_element_by_css_selector("span.glyphicon.glyphicon-ok").text)
        self.assertEqual("1", driver.find_element_by_css_selector("div.panel-body > div.row > div.col-md-10").text)
        driver.find_element_by_id("button_delete").click()
        driver.find_element_by_id("id_submit_keep").click()

        # assert that repository was not deleted
        self.assertEqual(self.project.repos.count(), 1)

        driver.find_element_by_link_text("Repositories").click()
        driver.find_element_by_link_text("Repository " + repo_path).click()
        self.assertEqual("", driver.find_element_by_css_selector("span.glyphicon.glyphicon-ok").text)
        self.assertEqual("1", driver.find_element_by_css_selector("div.panel-body > div.row > div.col-md-10").text)
        driver.find_element_by_id("button_delete").click()
        driver.find_element_by_id("id_submit_delete").click()
        driver.find_element_by_link_text("Repositories").click()
        self.assertNotIn("Repository " + repo_path, driver.page_source)
        driver.find_element_by_link_text("Board").click()
        driver.find_element_by_link_text("SLN-1").click()
        self.assertNotIn("initial commit", driver.page_source)

        # login again with developer account and assert that repositories tab is not displayed in settings
        client = Client()
        client.login(username='d', password='f')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

        driver.get('{}{}'.format(self.live_server_url,
                                 reverse('project:detail', kwargs={'project': self.project.name_short})))
        driver.find_element_by_id("project_edit").click()
        self.assertNotIn("Repositories", driver.page_source)

        shutil.rmtree(repo_path, ignore_errors=True)
        self.assertEqual(os.path.isdir(repo.get_local_repo_path()), False)
        self.assertEqual(os.path.isfile(repo.rsa_pub_path.path), False)
        self.assertEqual(os.path.isfile(repo.rsa_priv_path.path), False)
