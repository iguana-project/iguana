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
import re

from project.models import Project
from issue.models import Issue
from kanbancol.models import KanbanColumn
from tag.models import Tag
from django.contrib.auth import get_user_model

proj_short = 'PRJ'


class AutocompletetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('tast', 'test@testing2.com', 'test1234')
        cls.user3 = get_user_model().objects.create_user('tust', 'test@testing3.com', 'test1234')

        cls.project = Project(creator=cls.user, name_short=proj_short)
        cls.project.save()
        cls.project.developer.add(cls.user)

        cls.tag1 = Tag(project=cls.project, tag_text='backend', color='RED')
        cls.tag2 = Tag(project=cls.project, tag_text='frontend', color='BLUE')
        cls.tag1.save()
        cls.tag2.save()
        cls.kanbancol = KanbanColumn(project=cls.project, position=4, name='test')
        cls.kanbancol.save()

    def setUp(self):
        self.client.force_login(self.user)
        self.title1 = 'asdf'
        self.title2 = 'ghjk'
        # NOTE: this element gets modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.issue = Issue(project=self.project, title=self.title1,
                           due_date='2016-12-16', kanbancol=self.kanbancol, storypoints='3')
        self.issue.save()
        # NOTE: this element gets modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.issue2 = Issue(project=self.project, title=self.title2,
                            due_date='2016-12-16', kanbancol=self.kanbancol, storypoints='3')
        self.issue2.save()

    # create project(developer: all), edit project(developer: all, manager: all)
    def test_create_edit_project(self):
        # all user
        response = self.client.get(reverse('project:userac'))
        response_json = response.json()
        self.assertEqual(len(response.json()['results']), len(get_user_model().objects.all()))

    # shall return all developer for the provided project
    def test_create_edit_issue_assignee(self):
        response = self.client.get(reverse('project:userac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), len(self.project.developer.all()))
        self.project.developer.add(self.user2)
        response = self.client.get(reverse('project:userac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), len(self.project.developer.all()))

    # shall return all issues for the provided project
    def test_create_issue_dependsOn(self):
        response = self.client.get(reverse('project:issueac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), len(Issue.objects.filter(project=self.project)))

        new_issue = Issue(project=self.project, due_date='2017-12-16', kanbancol=self.kanbancol, storypoints='3')
        new_issue.save()
        response = self.client.get(reverse('project:issueac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), len(Issue.objects.filter(project=self.project)))

    # shall return the issue title for the provided issue number
    def test_edit_issue_dependsOn(self):
        response = self.client.get(reverse('project:issueac',
                                           kwargs={"project": proj_short, "issue": self.issue.number}))
        response_json = response.json()
        self.assertNotContains(response, self.title1)
        self.assertContains(response, self.title2)

    # shall return all tags for the provided project
    def test_create_edit_issue_tags(self):
        # number of tags for the project self.project with short name proj_short
        response = self.client.get(reverse('project:tagac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), len(Tag.objects.filter(project=self.project)))

        new_tag = Tag(project=self.project, tag_text='new_tag', color='YELLOW')
        new_tag.save()

        response = self.client.get(reverse('project:tagac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), len(Tag.objects.filter(project=self.project)))

    # shall return all user - not project related
    def test_user_filter(self):
        # number of user their name starts with 'te' - this is not project related
        response = self.client.get(reverse('project:userac')+'/?q=te')
        response_json = response.json()
        num_elements = 0
        for user in get_user_model().objects.all():
            if re.match("te.*", str(user)):
                num_elements += 1
        self.assertEqual(len(response_json['results']), num_elements)
        # number of user their name starts with 't' - this is not project related
        response = self.client.get(reverse('project:userac')+'/?q=t')
        response_json = response.json()
        num_elements = 0
        for user in get_user_model().objects.all():
            if re.match("t.*", str(user)):
                num_elements += 1
        self.assertEqual(len(response_json['results']), num_elements)

    # shall return all issues for the provided project
    def test_issue_filter(self):
        # number of issues containing 'j' in the title
        response = self.client.get(reverse('project:issueac', kwargs={"project": proj_short}) + '/?q=j')
        response_json = response.json()
        num_elements = 0
        for issue in Issue.objects.filter(project=self.project):
            if re.match(".*j.*", str(issue)):
                num_elements += 1
        self.assertEqual(len(response_json['results']), num_elements)
        self.assertNotContains(response, self.title1)
        self.assertContains(response, self.title2)

    # shall return all tags for the provided project
    def test_tag_filter(self):
        # tags their name contains 'end' in the tag_text for the project self.project with short name proj_short
        response = self.client.get(reverse('project:tagac', kwargs={"project": proj_short})+'/?q=end')
        response_json = response.json()
        num_elements = 0
        for tag in Tag.objects.filter(project=self.project):
            if re.match(".*end.*", str(tag)):
                num_elements += 1
        self.assertEqual(len(response_json['results']), num_elements)
        # tags their name contains 'ontend' in the tag_text for the project self.project with short name proj_short
        response = self.client.get(reverse('project:tagac', kwargs={"project": proj_short})+'/?q=ontend')
        response_json = response.json()
        num_elements = 0
        for tag in Tag.objects.filter(project=self.project):
            if re.match(".*ontend.*", str(tag)):
                num_elements += 1
        self.assertEqual(len(response_json['results']), num_elements)

    # there shall be no results if the user is logged out
    def test_logged_out(self):
        self.client.logout()

        # userac
        response = self.client.get(reverse('project:userac'))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

        # tagac
        response = self.client.get(reverse('project:issueac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

        # issueac
        response = self.client.get(reverse('project:tagac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

    # there shall be no results if the user is not part of the project
    def test_not_in_project(self):
        self.client.logout()
        self.client.force_login(self.user2)

        # userac
        response = self.client.get(reverse('project:userac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

        # tagac
        response = self.client.get(reverse('project:tagac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

        # issueac
        response = self.client.get(reverse('project:issueac', kwargs={"project": proj_short}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

        response = self.client.get(reverse('project:issueac',
                                           kwargs={"project": proj_short, "issue": self.issue.number}))
        response_json = response.json()
        self.assertEqual(len(response_json['results']), 0)

    # shall return no results but also should not crash or throw any exceptions
    def test_project_does_not_exist(self):
        # TODO TESTCASE
        # TODO userac
        # TODO tagac
        # TODO issueac
        pass

    # TODO TESTCASE same tests for search-autocomplete
