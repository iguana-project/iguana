"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase

from project.models import Project
from issue.models import Issue
from tag.models import Tag
from django.contrib.auth import get_user_model

from search.frontend import SearchFrontend


class IssueSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.manager.add(cls.user)
        cls.issue = Issue(title="Test-Issue",
                          project=cls.project,
                          kanbancol=cls.project.kanbancol.first(),
                          type="Bug")
        cls.issue.save()

        tag = Tag(tag_text='Test', project=cls.project)
        tag.save()
        cls.issue.tags.add(tag)

    def test_search_for_tag(self):
        result = SearchFrontend.query('test', self.user)
        self.assertEqual(len(result), 2)

        result = SearchFrontend.query('Issue.tags.tag_text ~~ "es"', self.user)
        self.assertEqual(len(result), 1)
