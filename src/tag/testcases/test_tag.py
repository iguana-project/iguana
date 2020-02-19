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

from django.db import IntegrityError
import re

from tag.views import TagView
from user_management.views import LoginView
from issue.models import Issue
from project.models import Project
from tag.models import Tag
from search.frontend import SearchFrontend
from django.contrib.auth import get_user_model, login
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


p0_name = 'project0'
p1_name = 'project1'
p0_short = 'aaaa'
p1_short = 'bbbb'


class TagTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        # create some projects
        p0 = Project(name=p0_name, name_short=p0_short, creator=self.user)
        p0.save()
        p0.manager.add(self.user)
        p0.save()

        p1 = Project(name=p1_name, name_short=p1_short, creator=self.user)
        p1.save()
        p1.manager.add(self.user)
        p1.save()
        self.client.force_login(self.user)

        self.p2 = Project(name="project2", name_short="p2", creator=self.user)
        self.p2.save()
        self.p2.manager.add(self.user)
        self.p2.save()

    # Helper function, that retrieves a color hex code by name.
    def get_color_by_name(self, name):
        d = {}
        for color, color_name in Tag.COLORS:
            d[color_name] = color
        return d[name]

    def test_tag_view_and_template(self):
        view_and_template(self, TagView, 'tag/tag_manage.html', 'tag:tag', address_kwargs={'project': p0_short})

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        redirect_to_login_and_login_required(self, 'tag:tag', address_kwargs={'project': p0_short})

    def test_form(self):
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}))
        form_data = {
            'create_tag': 'True',
        }
        response = self.client.post(reverse('tag:tag', kwargs={'project': p0_short}), form_data, follow=True)
        self.assertFormError(response, 'form', 'tag_text', 'This field is required.')
        self.assertTemplateUsed(response, 'tag/tag_manage.html')
        self.assertEqual(response.status_code, 200)

    def test_user_passes_test_mixin(self):
        proj_name = "project"
        proj_short = "cccc"
        project = Project(name=proj_name, name_short=proj_short, creator=self.user)
        project.save()
        proj_name2 = "project2"
        proj_short2 = "dddd"
        project2 = Project(name=proj_name2, name_short=proj_short2, creator=self.user)
        project2.save()

        # we neither add the user as manager nor as developer so there are not the necessary rights to manipulate tags
        response = self.client.get(reverse('tag:tag', kwargs={'project': proj_short}), follow=True)
        self.assertContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                      "login with an account that has access.")
        self.assertTemplateUsed(response, 'registration/login.html')

        # developer is good
        project.developer.add(self.user)
        project.save()
        response = self.client.get(reverse('tag:tag', kwargs={'project': proj_short}), follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                         "login with an account that has access.")

        # manager is good
        project2.manager.add(self.user)
        project2.save()
        response = self.client.get(reverse('tag:tag', kwargs={'project': proj_short2}), follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                         "login with an account that has access.")

    def test_only_project_specific_tags_manageable(self):
        # create tags for p0
        tag_texts = ['test-tag', 'test-2', 'test-tag3', '3-crap', 't-4_crap']
        tags = []
        for tag_text in tag_texts:
            tag = Tag(tag_text=tag_text, project=Project.objects.get(name_short=p0_short))
            tag.save()
            tags.append(tag)

        # p0 tags are not part of p1
        response = self.client.get(reverse('tag:tag', kwargs={'project': p1_short}), follow=True)
        for tag in tag_texts:
            self.assertNotContains(response, tag)

    def test_tags_are_unique_per_project(self):
        tag_text = "please_don't_duplicate_me"
        t0 = Tag(tag_text=tag_text, project=Project.objects.get(name_short=p0_short))
        t0.save()
        with self.assertRaises(IntegrityError):
            t1 = Tag(tag_text=tag_text, project=Project.objects.get(name_short=p0_short))
            t1.save()

    def test_issue_relation(self):
        # TODO TESTCASE
        pass

    def test_project_relation(self):
        # TODO TESTCASE
        pass

    def test_create_tags_with_get_request_not_possible(self):
        new_tag = "new_tag"
        form_data = {
            'tag_text': new_tag,
            'create_tag': 'True',
            'color': "",
        }
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # didn't add a tag
        self.assertNotContains(response, new_tag)

    # helper function: creates a tag and verify it appears afterwards
    def create_and_verify(self, new_tag, previous_tags):
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), follow=True)
        form_data = {
            'tag_text': new_tag,
            'create_tag': 'True',
            'color': "",
        }
        response = self.client.post(reverse('tag:tag', kwargs={'project': p0_short}), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_tag)
        for tag in previous_tags:
            self.assertContains(response, tag)

    # helper function: creates multiple tags and verify they appear afterwards
    def create_multiple_and_verify_once(self, new_tags, previous_tags):
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), follow=True)
        for tag in new_tags:
            form_data = {
                'tag_text': tag,
                'create_tag': 'True',
                'color': '',
            }
            response = self.client.post(reverse('tag:tag', kwargs={'project': p0_short}), form_data, follow=True)
        for tag in new_tags:
            self.assertContains(response, tag)
        for tag in previous_tags:
            self.assertContains(response, tag)

    def test_create_some(self):
        t0 = 'test-tag'
        t1 = 'test-2'
        t2 = 'test-tag3'
        previous_tags = []
        self.create_and_verify(t0, previous_tags)
        # TODO TESTCASE test tag-element-count
        previous_tags.append(t0)
        self.create_and_verify(t1, previous_tags)
        # TODO TESTCASE test tag-element-count
        previous_tags.append(t1)
        self.create_and_verify(t2, previous_tags)
        # TODO TESTCASE test tag-element-count

    # helper function: deletes a tag and verify everything but this appears afterwards
    def delete_and_verify(self, tag_to_delete, previous_tags):
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), follow=True)
        form_data = {
            'delete_tags': tag_to_delete,
            'tag_text': '',
            'create_tag': '',
        }
        response = self.client.post(reverse('tag:tag', kwargs={'project': p0_short}), form_data, follow=True)
        self.assertRedirects(response, reverse('tag:tag', kwargs={'project': p0_short}))
        self.assertNotContains(response, tag_to_delete)
        previous_tags.remove(tag_to_delete)
        for tag in previous_tags:
            self.assertContains(response, tag)

    def test_delete(self):
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), follow=True)
        t0 = 'test-tag_first'
        t1 = 'test-2'
        t2 = 'test-tag3'
        t3 = '3crap'
        t4 = 't-4_crap'
        new_tags = [t0, t1, t2, t3, t4]
        self.create_multiple_and_verify_once(new_tags, [])

        previous_tags = new_tags.copy()
        self.delete_and_verify(t1, previous_tags)
        # TODO TESTCASE test tag-element-count
        self.delete_and_verify(t3, previous_tags)
        # TODO TESTCASE test tag-element-count
        self.delete_and_verify(t0, previous_tags)
        # TODO TESTCASE test tag-element-count

    def test_delete_multiple_at_once(self):
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), follow=True)
        t0 = 'test-tag'
        t1 = 'test-2'
        t2 = 'test-tag3'
        t3 = '3crap'
        t4 = 't-4_crap'
        new_tags = [t0, t1, t2, t3, t4]
        self.create_multiple_and_verify_once(new_tags, [])

        # test delete them without any filling get request, but only posts
        previous_tags = new_tags.copy()
        delete_them = [t2, t4, t0, t1, t3]
        response = self.client.get(reverse('tag:tag', kwargs={'project': p0_short}), follow=True)
        for tag_to_delete in delete_them:
            form_data = {
                'delete_tags': tag_to_delete,
                'tag_text': '',
                'create_tag': '',
            }
            response = self.client.post(reverse('tag:tag', kwargs={'project': p0_short}), form_data, follow=True)
            previous_tags.remove(tag_to_delete)
            self.assertNotContains(response, tag_to_delete)
            for tag in previous_tags:
                self.assertContains(response, tag)

        # TODO TESTCASE delete multiple in one post-request
        # TODO this is not possible yet, since 'delete_tags' is used for all entries
        # TODO this might work with 'delete_tags': (t0, t1)
        """
        self.create_multiple_and_verify_once(new_tags, [])
        response = self.client.get(reverse('tag:tag'), follow=True)
        form_data = {
            'delete_tags': t0,
            'delete_tags': t3,
            'delete_tags': t1,
            'tag_text': '',
            'create_tag': '',
        }

        response = self.client.post(reverse('tag:tag'), form_data, follow=True)
        """

    # relative issues are listed in the tag-table
    def test_show_matching_issues_and_color(self):
        project_name = "project"
        project_short = "cccc"
        project = Project(name=project_name, name_short=project_short, creator=self.user)
        project.save()
        project.developer.add(self.user)
        project.save()
        yellow_text = "yellow"
        yellow = Tag(tag_text=yellow_text, color=self.get_color_by_name("yellow"), project=project)
        yellow.save()
        blue_text = "blue"
        blue = Tag(tag_text=blue_text, color=self.get_color_by_name("blue"), project=project)
        blue.save()
        red_text = "red"
        red = Tag(tag_text=red_text, color=self.get_color_by_name("red"), project=project)
        red.save()
        ye_issue_title = "ye_issue"
        yellow_issue = Issue(title=ye_issue_title, project=project)
        yellow_issue.save()
        yellow_issue.tags.add(yellow)
        yellow_issue.save()
        bl_issue_title = "bl_issue"
        blue_issue = Issue(title=bl_issue_title, project=project)
        blue_issue.save()
        blue_issue.tags.add(blue)
        blue_issue.save()
        re_issue_title = "re_issue"
        red_issue = Issue(title=re_issue_title, project=project)
        red_issue.save()
        red_issue.tags.add(blue)
        red_issue.save()
        ye_re_issue_title = "ye_re_issue"
        yellow_red_issue = Issue(title=ye_re_issue_title, project=project)
        yellow_red_issue.save()
        yellow_red_issue.tags.add(yellow)
        yellow_red_issue.tags.add(red)
        yellow_red_issue.save()
        response = self.client.get(reverse('tag:tag', kwargs={'project': project_short}), follow=True)
        text = response.content.decode()
        skip_color_choice = text.index("create_tag")

        # test yellow
        text_index = text[skip_color_choice:].index(yellow_text)+skip_color_choice
        # color
        style_start = text[skip_color_choice:text_index].rindex("div class")+skip_color_choice
        self.assertTrue(len(re.findall(self.get_color_by_name("yellow"), text[style_start:text_index])) == 1)
        # issue-relation
        # NOTE: Don't use title as search, because this element is not there if there are no issues for this tag
        #       that's y we determine the beginning and the end of the area where the issue-element should be
        color_start = text[text_index:].index("col-md-8 col-xs-5")+text_index
        color_end = text[color_start:].index("/div")+color_start
        color_values = re.findall(ye_issue_title, text[color_start:color_end])
        # two: one for the href-title and one for the actual issue-name
        self.assertTrue(len(color_values) == 2)

        # test blue
        text_index = text[skip_color_choice:].index(blue_text)+skip_color_choice
        # color
        style_start = text[skip_color_choice:text_index].rindex("div class")+skip_color_choice
        self.assertTrue(len(re.findall(self.get_color_by_name("blue"), text[style_start:text_index])) == 1)
        # issue-relation
        color_start = text[text_index:].index("col-md-8 col-xs-5")+text_index
        color_end = text[color_start:].index("/div")+color_start
        color_values = re.findall(bl_issue_title, text[color_start:color_end])
        self.assertTrue(len(color_values) == 2)

        # test red
        text_index = text[skip_color_choice:].index(red_text)+skip_color_choice
        # color
        style_start = text[skip_color_choice:text_index].rindex("div class")+skip_color_choice
        self.assertTrue(len(re.findall(self.get_color_by_name("red"), text[style_start:text_index])) == 1)
        # issue-relation
        color_start = text[text_index:].index("col-md-8 col-xs-5")+text_index
        color_end = text[color_start:].index("/div")+color_start
        color_values = re.findall(re_issue_title, text[color_start:color_end])
        self.assertTrue(len(color_values) == 2)

        # test yellow_red
        # test in yellow
        text_index = text[skip_color_choice:].index(yellow_text)+skip_color_choice
        color_start = text[text_index:].index("col-md-8 col-xs-5") + text_index
        color_end = text[color_start:].index("/div")+color_start
        color_values = re.findall(ye_re_issue_title, text[color_start:color_end])
        self.assertTrue(len(color_values) == 2)
        # test in red
        text_index = text[skip_color_choice:].index(red_text)+skip_color_choice
        color_start = text[text_index:].index("col-md-8 col-xs-5")+text_index
        color_end = text[color_start:].index("/div")+color_start
        color_values = re.findall(ye_re_issue_title, text[color_start:color_end])
        self.assertTrue(len(color_values) == 2)

    def test_random_colors(self):
        colors = set()
        for i in range(len(Tag.COLORS)):
            tag = Tag(tag_text=str(i), project=self.p2)
            tag.save()
            colors.add(tag.color)
        self.assertEqual(colors, set([a for a, b in Tag.COLORS]))

    def test_search_for_tag(self):
        tag1 = Tag(tag_text='Test', project=Project.objects.get(name_short=p0_short))
        tag1.save()
        tag2 = Tag(tag_text='Test-Tag', project=Project.objects.get(name_short=p0_short))
        tag2.save()

        result = SearchFrontend.query('test', self.user)
        self.assertEqual(len(result), 2)

        result = SearchFrontend.query('Test-Tag', self.user)
        self.assertEqual(len(result), 1)

        # test fieldcheckings
        result = SearchFrontend.query('Tag.project.name_short ~~ "a"', self.user)
        self.assertEqual(len(result), 0)

        # test permission check
        user = get_user_model().objects.create_user('b', 'b@b.com', 'b1234567')
        result = SearchFrontend.query('test', user)
        self.assertEqual(len(result), 0)
