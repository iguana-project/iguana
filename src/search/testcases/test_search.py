"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
import datetime
from django.utils import timezone
from django.urls import reverse

import ply.lex as lex

from search.views import SearchView, ResultView, AdvancedSearchView, SearchEditView,\
                         MakeSearchPersistentView, DelSearchPersistentView
from project.models import Project
import search.lexer
from search import parser
from search.frontend import SearchFrontend
from search.models import Search
from tag.models import Tag
from issue.models import Issue, Comment
from django.contrib.auth import get_user_model
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required, \
        user_doesnt_pass_test_and_gets_404


class SearchTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(SearchTest, cls).setUpClass()

        # this model attribute gets changed in the tests, so take a backup first
        cls.sf_backup = list(Project.searchable_fields)

    @classmethod
    def tearDownClass(cls):
        # rollback above changes
        Project.searchable_fields = cls.sf_backup

        super(SearchTest, cls).tearDownClass()

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.developer.add(cls.user)
        cls.project2 = Project(creator=cls.user, name_short='PROJ')
        cls.project2.save()
        cls.project2.developer.add(cls.user)
        cls.project2.developer.add(cls.user2)
        # create test data (They are needed for search-purpose only)
        cls.issue = Issue(title="Test-Issue",
                          project=cls.project,
                          kanbancol=cls.project.kanbancol.first(),
                          type="Bug")
        cls.issue.save()
        issue = Issue(title="Blub-Issue", project=cls.project, kanbancol=cls.project.kanbancol.first(), type="Bug")
        issue.save()
        issue = Issue(title="Bla-Issue", project=cls.project, kanbancol=cls.project.kanbancol.first(), type="Task")
        issue.save()

        cls.issuep2 = Issue(title="Bling-Issue",
                            project=cls.project2,
                            kanbancol=cls.project2.kanbancol.first(),
                            type="Task")
        cls.issuep2.due_date = datetime.date(2000, 1, 1)
        cls.issuep2.save()
        cls.search = Search("description", "*", cls.user)

    def test_view_and_template(self):
        # TODO post requests required
        # SearchView
        # view_and_template(self, SearchView, 'search/search.html', 'search:search')
        # ResultView
        # view_and_template(self, ResultView, 'search/result_view.html', 'search:resultpage')
        # AdvancedSearchView
        # view_and_template(self, AdvancedSearchView, 'search/advanced_search_list.html', 'search:advanced')
        # SearchEditView
        # view_and_template(self, SearchEditView, 'search/search_edit.html', 'search:edit',
        #                   address_kwargs={'sqn_sh': 1})
        # MakeSearchPersistentView
        # view_and_template(self, MakeSearchPersistentView, 'search/advanced_search_list.html', 'search:makepersistent')
        # DelSearchPersistentView
        # view_and_template(self, DelSearchPersistentView, 'search/advanced_search_list.html', 'search:delpersistent')
        # RecentQueriesView - TODO this doesn't exist anymore - which one represents this now?
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # SearchView
        redirect_to_login_and_login_required(self, 'search:search')
        # ResultView
        redirect_to_login_and_login_required(self, 'search:resultpage')
        # AdvancedSearchView
        redirect_to_login_and_login_required(self, 'search:advanced')
        # SearchEditView
        redirect_to_login_and_login_required(self, 'search:edit', address_kwargs={'sqn_sh': 1})
        # MakeSearchPersistentView
        redirect_to_login_and_login_required(self, 'search:makepersistent')
        # DelSearchPersistentView
        redirect_to_login_and_login_required(self, 'search:delpersistent')
        # RecentQueriesView - TODO this doesn't exist anymore - which one represents this now?

    def forms(self):
        # TODO TESTCASE
        # TODO RecentQueriesView
        # TODO ResultView - click results, filter etc
        # TODO AdvancedSearchView - click add and removed to/from saved expr (makepersistent, delpersistent)
        # TODO SearchEditView - also that the description field is necessary
        pass

    def test_permissions(self):
        expression = '(User.username ~~ "a")'
        q = SearchFrontend.query(expression, self.user)

        self.assertEqual(Search.objects.count(), 1)

        search = Search.objects.first()

        self.assertEqual(str(search), expression)

        self.assertEqual(search.user_has_read_permissions(self.user), True)
        self.assertEqual(search.user_has_write_permissions(self.user), True)

        self.assertEqual(search.user_has_read_permissions(self.user2), False)
        self.assertEqual(search.user_has_write_permissions(self.user2), False)

        # set user2 as creator => user1 should not have read / write permissions
        search.creator = self.user2
        search.save()

        self.assertEqual(search.user_has_read_permissions(self.user), False)
        self.assertEqual(search.user_has_write_permissions(self.user), False)

        # share with project2 => user2 has read but not write permissions
        search.creator = self.user
        search.save()

        search.shared_with.add(self.project2)

        self.assertEqual(search.user_has_read_permissions(self.user2), True)
        self.assertEqual(search.user_has_write_permissions(self.user2), False)

        # share with project => user2 has no read and write permissions
        search.shared_with.clear()
        search.shared_with.add(self.project)

        self.assertEqual(search.user_has_read_permissions(self.user2), False)
        self.assertEqual(search.user_has_write_permissions(self.user2), False)

    def test_lexer(self):
        lexer = lex.lex(module=search.lexer)

        # contains test strings and their number of tokens
        tests = {
            '': 0,
            'AND': 1,
            'OR': 1,
            '() AND () OR ()': 8,
            'aa': 1,
            '20160314': 1,
            '15': 1,
            '==': 1,
            '>=': 1,
            '<': 1,
            '(A__A != 15) AND (B.B == "blub") OR (C__C ~ "bla")': 17,
        }

        for t in tests:
            lexer.input(t)

            count = 0
            for tok in lexer:
                count += 1

            self.assertEqual(count, tests[t])

    def test_parser(self):
        user = self.user
        project = self.project
        project2 = self.project2

        # contains expressions and the expected size of the resulting queryset
        tests = {
            'Project.name_short == "PRJ"': 1,
            'Project.issue.title ~~ "Issue"': 2,
            'Issue.type == "Bug"': 2,
            'Issue.type != "Bug"': 2,
            'Issue.number >= 2': 2,
            'Issue.number >= 2 LIMIT 1': 1,
            'Issue.number >= 2 SORT ASC Issue.number LIMIT 2': 2,
            'Issue.number >= 2 LIMIT 2 SORT ASC Issue.number': 2,
            'Issue.due_date <= 20051005': 1,
            '(Project.name_short ~~ "PRJ") AND (Project.issue.title == "Blub-Issue")': 1,
            '(Issue.project.name_short ~~ "PRJ") AND (Issue.title ~~ "Issue")': 3,
            '(Issue.project.name_short ~~ "PR") AND (Issue.title ~~ "Issue")': 4,
            '(Issue.project.name_short ~~ "PR") OR (Issue.title ~~ "Bling")': 4,
            '(Issue.project.name_short ~~ "PR") OR (Issue.title ~~ "Bling") SORT ASC Issue__number': 4,
            '(Issue.project.name_short ~~ "PR") OR (Issue.title ~~ "Bling") SORT DESC Issue__number': 4,
            '(Issue.project.name_short ~~ "PR") OR (Issue.title ~~ "Bling") LIMIT 3': 3,
            'Comment.text == "blub"': 0,
            '(User.username ~~ "a")': 1,
        }

        for t in tests:
            q = SearchFrontend.query(t, user)
            self.assertEqual(len(q), tests[t])
            self.assertEqual(Search.objects.filter(creator=user, searchexpression=t).count(), 1)

        # check minlength checking
        self.assertRaises(ValueError, SearchFrontend.query, 'aa', user)
        # minlength checking must also work when combining
        # short expressions by AND or OR with valid expressions
        self.assertRaises(ValueError, SearchFrontend.query, 'Bla AND   OR Blub', user)
        self.assertRaises(ValueError, SearchFrontend.query, 'Bla OR   OR Blub', user)
        self.assertRaises(ValueError, SearchFrontend.query, 'Bla OR   AND Blub', user)

        # check duplicate checking
        expression = 'Issue.type == "Bug"'
        q = SearchFrontend.query(expression, user)
        self.assertEqual(len(q), 2)
        self.assertEqual(Search.objects.filter(creator=user, searchexpression=expression).count(), 1)

        # assert that non-persistent searches are removed from model
        self.assertEqual(Search.objects.filter(creator=user, persistent=False).count(), 10)

        # expressions that shall not be stored in the database
        tests = {
            # fulltext searches
            'iss': 4,
            'Blu AND iss': 1,
            'Blu AND iss OR Bla AND iss OR Bli AND iss': 3,
            'Bli AND lin AND sue': 1,
            'Bling OR Bla': 2,
            'Bli OR Iss AND Bla': 2,
            # broken regexes
            'Comment.text ~ "?{42}.': 0,
        }

        for t in tests:
            q = SearchFrontend.query(t, user)
            self.assertEqual(len(q), tests[t])
            self.assertEqual(Search.objects.filter(creator=user, searchexpression=t).count(), 0)

        # negative tests
        tests = [
            'Project.name_short == "PRJ" AND OR Project.namme ~~ "T"',
            'Issue.due_date >= 20121340',
            'Issue.due_date >= 20100101 SORT Issue.number',
            'Issue.due_date >= 20100101 SORT ASC',
            'Issue.due_date >= 20100101 LIMIT',
            'Project.name <> "PRJ"',
            'Project.name <= PRJ',
            'Project.name',
            'LIMIT 3',
            'Project.invalidfield ~~ "blubber"',
            'Invalidobject.field ~~ "blubber"',
        ]

        for t in tests:
            self.assertRaises(Exception, parser.compile, t)

        # set searchable_fields to invalid values and check behavior
        Project.searchable_fields.append('invalidfield')
        self.assertRaises(Exception, parser.compile, 'Project.invalidfield ~~ "blubber"')
        Project.searchable_fields = []
        q = SearchFrontend.query('blubber', user)
        self.assertEqual(len(q), 0)

        # assert that non-persistent searches are removed from model
        self.assertEqual(Search.objects.filter(creator=user, persistent=False).count(), 10)

    def test_fulltext_search(self):
        q = SearchFrontend.query('Issue', self.user)
        self.assertEqual(len(q), 4)
        q = SearchFrontend.query('iSSuE', self.user)
        self.assertEqual(len(q), 4)
        q = SearchFrontend.query('pro', self.user)
        self.assertEqual(len(q), 1)
        q = SearchFrontend.query('pRo', self.user)
        self.assertEqual(len(q), 1)

    def test_constraints(self):
        comment = Comment(creator=self.user2,
                          issue=self.issuep2,
                          text="blub, sehr kreativ",
                          when=timezone.now())
        comment.save()
        comment = Comment(creator=self.user,
                          issue=self.issue,
                          text="blub",
                          when=timezone.now())
        comment.save()

        # contains expressions and the expected size of the resulting queryset
        tests = {
            'Project.name_short == "PRJ"': 0,
            'Project.issue.title ~~ "Issue"': 1,
            'Issue.type == "Bug"': 0,
            '(Issue.project.name_short ~~ "PR") OR (Issue.title ~~ "Bling")': 1,
            'Comment.text ~~ "blub"': 1,
            'Comment.text ~ "b.{2}b"': 1,
        }

        # use user2 for query this time (has only access to 2nd project)
        for t in tests:
            q = SearchFrontend.query(t, self.user2)
            self.assertEqual(len(q), tests[t])
            self.assertEqual(Search.objects.filter(creator=self.user2, searchexpression=t).count(), 1)

    def test_change_persistence(self):
        SearchFrontend.query('Project.name_short == "PRJ"', self.user)

        # we now should have a non-persistent search
        self.assertEqual(Search.objects.filter(creator=self.user).count(), 1)

        self.client.force_login(self.user)
        response = self.client.post(reverse('search:makepersistent'), {'pk': '1'})
        self.assertRedirects(response, reverse('search:advanced'))
        self.assertEqual(Search.objects.filter(creator=self.user, persistent=True).count(), 1)

        # try using already persistent object (should lead to 404)
        response = self.client.post(reverse('search:makepersistent'), {'pk': '1'})
        self.assertEqual(response.status_code, 404)

        # should also work for missing pks
        user_doesnt_pass_test_and_gets_404(self, 'search:makepersistent', get_kwargs={'pk': '2'})

        # test deleting persistent items
        response = self.client.post(reverse('search:delpersistent'), {'pk': '1'})
        self.assertRedirects(response, reverse('search:advanced'))
        self.assertEqual(Search.objects.filter(creator=self.user).count(), 0)

        # try deleting non-persistent item (should lead to 404)
        SearchFrontend.query('Project.name_short == "PRJ"', self.user)
        self.assertEqual(Search.objects.get(pk='2').persistent, False)
        response = self.client.post(reverse('search:delpersistent'), {'pk': '2'})
        self.assertEqual(response.status_code, 404)

        # try deleting non-present pk
        user_doesnt_pass_test_and_gets_404(self, 'search:delpersistent', get_kwargs={'pk': '3'})

    def test_share_with_project_0(self):
        expression = 'User.username ~ "a"'
        SearchFrontend.query(expression, self.user)

        # we now should have a non-persistent search
        self.assertEqual(Search.objects.filter(creator=self.user).count(), 1)

        self.client.force_login(self.user)
        response = self.client.post(reverse('search:makepersistent'), {'pk': '1'})
        self.assertRedirects(response, reverse('search:advanced'))
        self.assertEqual(Search.objects.filter(creator=self.user, persistent=True).count(), 1)

        search = Search.objects.first()
        search.shared_with.add(self.project)

        # we are creator of search, modifying should work
        description = 'new description'
        response = self.client.post(reverse('search:edit', kwargs={'sqn_sh': '1'}),
                                    {'description': description, 'searchexpression': expression},
                                    )
        self.assertRedirects(response, reverse('search:advanced'))

        search.refresh_from_db()
        self.assertEqual(search.description, description)

        # try with different creator, should not work
        search.creator = self.user2
        search.save()

        description = 'another description'
        user_doesnt_pass_test_and_gets_404(self, 'search:edit', address_kwargs={'sqn_sh': '1'},
                                           get_kwargs={'description': description, 'searchexpression': expression})

        search.refresh_from_db()
        self.assertNotEqual(search.description, description)

        # make user a manager for the project the search is shared with => should work
        search.shared_with.add(self.project)
        self.project.manager.add(self.user)

        description = 'even another description'
        response = self.client.post(reverse('search:edit', kwargs={'sqn_sh': '1'}),
                                    {'description': description, 'searchexpression': expression},
                                    follow=True,
                                    )
        self.assertRedirects(response, reverse('search:advanced'))

        search.refresh_from_db()
        self.assertEqual(search.description, description)

    def test_share_with_project(self):
        expression = 'User.username ~ "a"'
        SearchFrontend.query(expression, self.user)

        # we now should have a non-persistent search
        self.assertEqual(Search.objects.filter(creator=self.user).count(), 1)

        search = Search.objects.first()
        search.persistent = True
        search.shared_with.add(self.project)
        search.save()

        self.client.force_login(self.user2)
        user_doesnt_pass_test_and_gets_404(self, 'project:search', address_kwargs={'project': 'PRJ'})

        self.assertEqual(Search.objects.filter(creator=self.user, persistent=True).count(), 1)

    def test_search_for_tag(self):
        tag = Tag(tag_text='Test', project=self.project)
        tag.save()
        self.issue.tags.add(tag)

        result = SearchFrontend.query('test', self.user)
        self.assertEqual(len(result), 2)

        result = SearchFrontend.query('Issue.tags.tag_text ~~ "es"', self.user)
        self.assertEqual(len(result), 1)

    # TODO TESTCASE search for different types and use extended searches

    def test_filter(self):
        # TODO TESTCASE test project filter
        # TODO TESTCASE test type filter
        # TODO TESTCASE test both filters
        pass

    def test_tag_filter(self):
        # TODO TESTCASE verify the project of tags and comments is part of the result
        # TODO TESTCASE verify the type is part of the result as soon as no type filter is active
        pass
