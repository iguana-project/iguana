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

import ply.lex as lex
import issue.lexer
from issue import parser

from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue
from tag.models import Tag
from sprint.models import Sprint
from timelog.models import Timelog
from django.contrib.auth import get_user_model
from django.db.models import Q


class FormTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.user.first_name = 'Alice'
        self.user.last_name = 'Bla'
        self.user.save()
        self.user2 = get_user_model().objects.create_user('d', 'e', 'f')
        self.user2.first_name = 'Bob'
        self.user2.last_name = 'Blub'
        self.user2.save()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project2 = Project(creator=self.user, name_short='TPJ')
        self.project2.save()
        self.project.developer.add(self.user)
        self.project2.developer.add(self.user)
        self.project.developer.add(self.user2)
        kanbancol = KanbanColumn(project=self.project, position=4, name='ReallyDone')
        kanbancol.save()

    def test_lexer(self):
        lexer = lex.lex(module=issue.lexer)

        # contains test strings and their expected number of tokens
        tests = {
            '': 0,
            'blubber blub': 1,
            ' ~ISU-42': 1,
            ' ~42': 1,
            ' !4': 1,
            ' :Story': 1,
            ' #tag42': 1,
            ' #ta g42': 1,
            ' @user1234': 1,
            '>ISU-1337': 1,
            '>1337': 1,
            '>ISU-1337 @user !2 #1tag :Bug ~ISU-1': 6,
            'fancy text ~ISU-2 :Task': 3,
            'fancy te(x(t w)ith (Braces) ~ISU-2 :Task': 3,
            'another te(x(t w)ith (Braces( ~ISU-2 :Task': 3,
            'tes-_.?",/t-_.?" ~ISU-42': 2,
            '>ISU-42 +2d15h10m': 2,
            'blubber +': 2,
            '>ISSU-42 $10': 2,
            'Issue with ;fancy description': 2,
            '>ISSU-42 ;edit description': 2,
            'Issue with &Column': 2,
            'Bla ;(öaa)': 2,
        }

        for t in tests:
            lexer.input(t)

            count = 0
            for tok in lexer:
                count += 1

            self.assertEqual(count, tests[t])

        # negative tests
        tests = [
            ':Story',
            '#tag',
            '#tag#tag',
            '@user#tag',
            ' :Storyy',
            ' :Bugg',
            'fancy text@user',
            'test! ~ISU42',
            ' ~ISSUE-42',
            ' ~ISS42',
            '>Iss-1 +2m5h',
            '>ISS-1 $15b',
            '>ISS-1 ;',
            '>ISS-1 &',
        ]

        for t in tests:
            lexer.input(t)

            self.assertRaises(Exception, eval_lex_xpr, lexer)

    def test_parser(self):
        # contains test strings and the expected length of the attrs_to_set list
        # the third field indicates whether an issue shoud have been created
        tag = Tag(project=self.project, tag_text="testtag")
        tag.save()
        tag2 = Tag(project=self.project, tag_text="zweitertag")
        tag2.save()

        tests = [
            ['Fancy task :Task &Todo', 2, True],
            ['Another fancy task :Bug !2 #testtag @a ;with description', 5, True],
            ['>PRJ-1 !2 :Bug', 2, False],
            ['>2 $8', 1, False],
        ]

        for t in tests:
            parser.compile(t[0], self.project, self.user)
            self.assertEqual(len(parser.attrs_to_set), t[1])
            self.assertEqual(parser.issue_created, t[2])
            # all the above expressions should set issue_changed to True
            self.assertEqual(parser.issue_changed, True)

        # now we should have two new issues, check also their numbers
        self.assertEqual(Project.objects.first().issue.count(), 2)
        self.assertEqual(Issue.objects.filter(title="Fancy task").count(), 1)
        self.assertEqual(Issue.objects.filter(project=self.project, number=1).count(), 1)
        self.assertEqual(Issue.objects.filter(project=self.project, number=1).first().creator, self.user)
        self.assertEqual(Issue.objects.filter(project=self.project, number=1).first().kanbancol.name, 'Todo')
        self.assertEqual(Issue.objects.filter(project=self.project, number=2).count(), 1)
        self.assertEqual(Issue.objects.filter(project=self.project, number=2).first().storypoints, 8)
        self.assertEqual(Issue.objects.filter(project=self.project, number=2).first().description, 'with description')
        self.assertEqual(Issue.objects.filter(project=self.project, number=2).first().creator, self.user)

        # validate that fancy task is of type bug
        self.assertEqual(Issue.objects.filter(title="Fancy task",
                                              type="Bug").count(), 1)

        # validate that Another fancy task is of type bug with given attributes
        self.assertEqual(Issue.objects.filter(title="Another fancy task",
                                              type="Bug",
                                              priority=2,
                                              assignee=self.user,
                                              tags=tag).count(), 1)

        # set description of Another fancy task
        parser.compile('>PRJ-2 ;new description', self.project, self.user)
        self.assertEqual(Issue.objects.filter(project=self.project, number=2).first().description, 'new description')

        # set kanbancol of Fancy task
        parser.compile('>PRJ-1 &Progr', self.project, self.user)
        self.assertEqual(Issue.objects.filter(project=self.project, number=1).first().kanbancol.name, 'In Progress')

        # test icontains when setting kanbancol
        self.assertRaises(Exception, parser.compile, '>PRJ-1 &done', self.project, self.user)
        self.assertEqual(Issue.objects.filter(project=self.project, number=1).first().kanbancol.name, 'In Progress')

        parser.compile('>PRJ-1 &Done', self.project, self.user)
        self.assertEqual(Issue.objects.filter(project=self.project, number=1).first().kanbancol.name, 'Done')

        # add second tag and new asignee to PRJ2 and validate
        currentID = self.project.nextTicketId
        parser.compile('>PRJ-2 #zweitertag @d', self.project, self.user)
        issue = Issue.objects.get(title="Another fancy task")
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(parser.issue_to_change, issue)
        self.assertEqual(issue.tags.count(), 2)
        self.assertEqual(issue.assignee.count(), 1)
        self.assertEqual(issue.assignee.first(), self.user2)
        self.assertEqual(issue.number, 2)
        self.project.refresh_from_db()
        self.assertEqual(currentID, self.project.nextTicketId)

        # test permission checks and validations
        user = get_user_model().objects.create_user('g', 'h', 'i')
        issue.tags.clear()
        issue.refresh_from_db
        self.assertEqual(issue.tags.count(), 0)

        # not existing issues may not be edited and nextTicketId must not change
        currentID = self.project.nextTicketId
        self.assertRaises(Exception, parser.compile, '>PRJ-3 #zweitertag @d', self.project, self.user)
        self.project.refresh_from_db()
        self.assertEqual(currentID, self.project.nextTicketId)

        # user must not edit projects to which he has no devel access
        self.assertRaises(Exception, parser.compile, '>PRJ-2 #zweitertag @d', self.project, user)

        # only users with access to project may be set as asignee
        self.assertRaises(Exception, parser.compile, '>PRJ-2 #zweitertag @g', self.project, self.user)

        # tags must not have changed
        issue.refresh_from_db
        self.assertEqual(issue.tags.count(), 0)

        # create another tag containing a space
        tag = Tag(project=self.project, tag_text="tag with spaces")
        tag.save()
        parser.compile('>PRJ-2 #tag with spaces @d', self.project, self.user)
        self.assertEqual(parser.issue_changed, True)
        issue.refresh_from_db()
        self.assertEqual(issue.tags.filter(pk=tag.pk).count(), 1)

        # dependent issue must exist and be in the same project
        parser.compile('Test-Issue proj2 :Bug', self.project2, self.user)
        self.assertEqual(parser.issue_created, True)
        self.assertEqual(parser.issue_changed, True)
        issue = Issue.objects.get(title="Test-Issue proj2")
        self.assertEqual(parser.issue_to_change, issue)
        self.assertEqual(Issue.objects.filter(project=self.project2).count(), 1)
        self.assertRaises(Exception, parser.compile, '>TPJ-1 ~PRJ-1', self.project, self.user)

        # log time to issue
        parser.compile('>PRJ-1 +2h5m', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        # logging time is no change action
        self.assertEqual(parser.issue_changed, False)
        t = Timelog.objects.get(issue__title='Fancy task')
        self.assertEqual(t.time.total_seconds(), 7500)

        # log many times to issue
        parser.compile('>PRJ-1 +2h5m +1m', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, False)
        self.assertEqual(Timelog.objects.filter(issue__title='Fancy task').count(), 3)
        totaltime = 0
        for log in Timelog.objects.filter(issue__title='Fancy task'):
            totaltime += log.time.total_seconds()
        self.assertEqual(totaltime, 15060)

        # log time to new issue
        issuetitle = 'Timelog-test-issue'
        parser.compile(issuetitle + ' +2h5m', self.project, self.user)
        self.assertEqual(parser.issue_created, True)
        self.assertEqual(parser.issue_changed, False)
        self.assertEqual(Issue.objects.filter(title=issuetitle).count(), 1)
        t = Timelog.objects.get(issue__title=issuetitle)
        self.assertEqual(t.time.total_seconds(), 7500)

        # test empty timelog field (must not create new timelog object, should still be 3)
        parser.compile('>PRJ-1 +', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, False)
        self.assertEqual(Timelog.objects.filter(issue__title='Fancy task').count(), 3)

        # some syntactic stuff that should fail
        tests = [
            'Test-String ',
            '> @a',
            '>PRJ-2',
        ]

        for t in tests:
            self.assertRaises(Exception, parser.compile, t, self.project, self.user)

        # tests for contains checks of tag
        Issue.objects.get(title='Fancy task').tags.clear()
        self.assertRaises(Exception, parser.compile, '>PRJ-1 #tag', self.project, self.user)
        self.assertEqual(Issue.objects.get(title='Fancy task').tags.count(), 0)
        parser.compile('>PRJ-1 #ttag', self.project, self.user)
        self.assertEqual(Issue.objects.get(title='Fancy task').tags.count(), 1)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)

        tag3 = Tag(project=self.project, tag_text="ttag")
        tag3.save()
        parser.compile('>PRJ-1 #ttag', self.project, self.user)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.filter(tags=tag3).count(), 1)
        self.assertEqual(Issue.objects.get(title='Fancy task').tags.count(), 2)

        # check that searching for tag is case insensitive
        Issue.objects.get(title='Fancy task').tags.clear()
        parser.compile('>PRJ-1 #teStTaG', self.project, self.user)
        self.assertEqual(Issue.objects.get(title='Fancy task').tags.count(), 1)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)

        # same for user
        Issue.objects.get(title='Fancy task').assignee.clear()
        user3 = get_user_model().objects.create_user('jj', 'x', 'x')
        self.project.developer.add(user3)
        user4 = get_user_model().objects.create_user('jjj', 'y', 'y')
        self.project.developer.add(user4)
        user5 = get_user_model().objects.create_user('kj', 'z', 'z')
        self.project.developer.add(user5)
        self.assertRaises(Exception, parser.compile, '>PRJ-1 @j', self.project, self.user)
        self.assertEqual(Issue.objects.get(title='Fancy task').assignee.count(), 0)
        parser.compile('>PRJ-1 @jj', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.filter(title='Fancy task',
                                              assignee=user3).count(), 1)
        parser.compile('>PRJ-1 @jjj', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.filter(title='Fancy task',
                                              assignee=user4).count(), 1)

        # user search case insensitive
        Issue.objects.get(title='Fancy task').assignee.clear()
        parser.compile('>PRJ-1 @jJJ', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.filter(title='Fancy task',
                                              assignee=user4).count(), 1)

        # check that setting more than one asignee is possible
        parser.compile('>PRJ-1 @a @jj @kj', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.get(title='Fancy task').assignee.count(), 3)
        parser.compile('>PRJ-1 @jj', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.get(title='Fancy task').assignee.count(), 1)

        # test add depends functionality
        parser.compile('New issue depending on PRJ-1 ~PRJ-1', self.project, self.user)
        self.assertEqual(parser.issue_created, True)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.filter(project=self.project, title='New issue depending on PRJ-1').count(), 1)
        self.assertEqual(Issue.objects.get(project=self.project,
                                           title='New issue depending on PRJ-1'
                                           ).dependsOn.count(), 1)
        parser.compile('>PRJ-1 ~PRJ-2', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.get(title='Fancy task').dependsOn.count(), 1)

        # tag not existant
        Issue.objects.get(title='Fancy task').tags.clear()
        self.assertRaises(Exception, parser.compile, '>PRJ-1 #imnothere', self.project, self.user)
        self.assertEqual(Issue.objects.get(title='Fancy task').tags.count(), 0)

        # user not existant
        Issue.objects.get(title='Fancy task').assignee.clear()
        self.assertRaises(Exception, parser.compile, '>PRJ-1 @imnothere', self.project, self.user)
        self.assertEqual(Issue.objects.get(title='Fancy task').assignee.count(), 0)

        # test omitting project shortname in depends and modify tag
        Issue.objects.get(title='Fancy task').dependsOn.clear()
        parser.compile('>1 ~2', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(Issue.objects.get(title='Fancy task').dependsOn.count(), 1)
        self.assertEqual(Issue.objects.get(title='Fancy task').dependsOn.first().title, 'Another fancy task')

        # check permissions test for issue to modify
        user5 = get_user_model().objects.create_user('tt', 'hh', 'ii')
        self.assertNotEqual(Issue.objects.get(title='Fancy task').priority, 4)
        self.assertRaises(Exception, parser.compile, '>1 !4', self.project, user5)
        self.assertNotEqual(Issue.objects.get(title='Fancy task').priority, 4)

        # check that managers and (managers & developers) are valid as asignee
        u_manager = get_user_model().objects.create_user('manager', 'ma', 'ma')
        u_maneloper = get_user_model().objects.create_user('maneloper', 'mar', 'mar')
        self.project.manager.add(u_manager)
        self.project.manager.add(u_maneloper)
        self.project.developer.add(u_maneloper)

        Issue.objects.get(title='Fancy task').assignee.clear()
        parser.compile('>PRJ-1 @manager @maneloper', self.project, self.user)
        self.assertEqual(parser.issue_created, False)
        self.assertEqual(parser.issue_changed, True)
        self.assertEqual(Issue.objects.filter(Q(title='Fancy task') &
                                              (Q(assignee=u_manager) | Q(assignee=u_maneloper))).count(), 2)

        # check that first and last name is also valid when searching for users
        parser.compile('>PRJ-1 @alice @bob', self.project, self.user)
        issue = self.project.issue.get(number=1)
        self.assertIn(self.user, issue.assignee.all())
        self.assertIn(self.user2, issue.assignee.all())
        parser.compile('>PRJ-1 @alice @Blub', self.project, self.user)
        issue.refresh_from_db()
        self.assertIn(self.user, issue.assignee.all())
        self.assertIn(self.user2, issue.assignee.all())

        # check that user is not assigned more than once
        parser.compile('>PRJ-1 @alice @Bla', self.project, self.user)
        issue.refresh_from_db()
        self.assertIn(self.user, issue.assignee.all())
        self.assertEqual(issue.assignee.count(), 1)

        # check that no issue is created with error in change expression
        self.project.refresh_from_db()
        currentID = self.project.nextTicketId
        currentTicketCount = self.project.issue.count()
        self.assertRaises(Exception, parser.compile, 'New Issue #nonexistanttag', self.project, self.user)
        self.project.refresh_from_db()
        self.assertEqual(currentID, self.project.nextTicketId)
        self.assertEqual(currentTicketCount, self.project.issue.count())

        # check that issue creation without change expression is possible
        self.project.refresh_from_db()
        currentID = self.project.nextTicketId
        currentTicketCount = self.project.issue.count()
        title = 'Fancy new issue without chgxpr'
        parser.compile(title, self.project, self.user)
        self.assertEqual(parser.issue_created, True)
        self.assertEqual(parser.issue_changed, False)
        self.project.refresh_from_db()
        self.assertEqual(self.project.issue.filter(title=title).count(), 1)
        self.assertEqual(currentID + 1, self.project.nextTicketId)
        self.assertEqual(currentTicketCount + 1, self.project.issue.count())

        # check that changing an issue without change expression throws an exception
        self.assertRaises(Exception, parser.compile, '>1', self.project, self.user)

    def test_olea_frontend(self):
        self.client.force_login(self.user)
        self.project.refresh_from_db()

        # test creating issue without sprint
        values = {
            'expression': 'Task from frontend @a',
            'currentsprint': '',
            'next': reverse('issue:backlog', kwargs={'project': self.project.name_short}),
        }
        response = self.client.post(reverse('issue:processOlea', kwargs={'project': self.project.name_short}), values)
        self.assertRedirects(response, values['next'])
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('oleaexpression', self.client.session)
        self.assertNotIn('oleafocus', self.client.session)
        self.assertEqual(Issue.objects.filter(project=self.project,
                                              title="Task from frontend",
                                              assignee=self.user).count(), 1)
        issue = Issue.objects.get(project=self.project, title="Task from frontend")
        self.assertEqual(issue.sprint, None)
        self.assertEqual(issue.number, 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.issue.count(), 1)
        self.assertEqual(self.project.nextTicketId, 2)

        # test creation with sprint
        sprint = Sprint(project=self.project)
        sprint.save()
        sprint2 = Sprint(project=self.project)
        sprint2.save()

        values['currentsprint'] = sprint.seqnum
        values['expression'] = 'Another frontend task @a'
        response = self.client.post(reverse('issue:processOlea', kwargs={'project': self.project.name_short}), values)
        self.assertNotIn('oleaexpression', self.client.session)
        self.assertIn('oleafocus', self.client.session)
        self.assertEqual(self.client.session['oleafocus'], 'autofocus')
        self.assertRedirects(response, values['next'])
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Issue.objects.filter(project=self.project,
                                              title="Another frontend task",
                                              assignee=self.user).count(), 1)
        issue = Issue.objects.get(project=self.project, title="Another frontend task")
        self.project.refresh_from_db()
        self.assertEqual(self.project.issue.count(), 2)
        self.assertEqual(issue.sprint, sprint)
        self.assertEqual(issue.number, 2)

        # test editing issue with currentsprint set (should not change sprint)
        issue = Issue.objects.get(project__name_short="PRJ", number=1)
        self.assertEqual(issue.sprint, None)
        values['expression'] = '>PRJ-1 @a'
        response = self.client.post(reverse('issue:processOlea', kwargs={'project': self.project.name_short}), values)
        self.assertIn('oleafocus', self.client.session)
        self.assertEqual(self.client.session['oleafocus'], 'autofocus')
        self.assertRedirects(response, values['next'])
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('oleafocus', self.client.session)
        issue.refresh_from_db()
        self.assertEqual(issue.sprint, None)

        # set sprint for issue and try again
        issue.sprint = sprint2
        issue.save()
        values['expression'] = '>PRJ-1 @a'
        response = self.client.post(reverse('issue:processOlea', kwargs={'project': self.project.name_short}), values)
        self.assertIn('oleafocus', self.client.session)
        self.assertEqual(self.client.session['oleafocus'], 'autofocus')
        self.assertRedirects(response, values['next'])
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(values['expression'], response.content.decode())
        self.assertNotIn('oleafocus', self.client.session)
        issue.refresh_from_db()
        self.assertEqual(issue.sprint, sprint2)

        # check that syntax errors are signalled by message
        values['expression'] = '>PRJ-1:! @a'
        response = self.client.post(reverse('issue:processOlea',
                                            kwargs={'project': self.project.name_short}
                                            ), values, follow=True)
        self.assertIn('&gt;PRJ-1:! @a', response.content.decode())
        self.assertRedirects(response, values['next'])
        self.assertEqual(len(list(response.context['messages'])), 1)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('oleaexpression', self.client.session)
        self.assertNotIn('oleafocus', self.client.session)

        # supply invalid sprint id
        values['expression'] = 'This is actually correct @a'
        values['currentsprint'] = '42'
        response = self.client.post(reverse('issue:processOlea',
                                            kwargs={'project': self.project.name_short}
                                            ), values, follow=True)
        self.assertRedirects(response, values['next'])
        self.assertIn(values['expression'], response.content.decode())
        self.assertNotIn('oleafocus', self.client.session)
        self.assertEqual(len(list(response.context['messages'])), 1)
        self.assertEqual(response.status_code, 200)
        issue = Issue.objects.get(project=self.project, title="This is actually correct")
        self.assertEqual(issue.sprint, None)


def eval_lex_xpr(lexer):
    for tok in lexer:
                pass
