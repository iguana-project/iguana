"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from glob import glob
import re
import os
from graphviz import Digraph

from django.core.management.base import BaseCommand
from django.urls import resolve, reverse, RegexURLResolver, RegexURLPattern


template_to_view = {
    'registration/sign_up.html': 'SignUpView',
    'registration/login.html': 'LoginView',
    'invite_users/invite_users.html': 'InviteUserView',
    'invite_users/successfully_invited.html': 'SuccessView',
    'project/project_list.html': 'Project_List_All',
    'project/project_create.html': 'Project_Create_View',
    'project/project_detail.html': 'Project_Detail_View',
    'project/project_timelog_detail.html': 'Project_User_Timelog_View',
    'project/project_timelog.html': 'Project_Detail_Timelog_View',
    'project/project_edit.html': 'Project_Edit_View',
    'project/project_confirm_delete.html': 'Project_Delete_View',
    'kanbancol/kanbancolumn_form.html': 'KanbanColumnUpdate',
    'kanbancol/kanbancolumn_confirm_delete.html': 'KanbanColumnDelete',
    'kanbancol/kanbancolumn_detail.html': 'KanbanColumnDetail',
    'integration/slackintegration_form.html': 'SlackIntegrationCreate',
    'integration/slackintegration_detail.html': 'SlackIntegrationDetail',
    'integration/slackintegration_form.html': 'SlackIntegrationUpdate',
    'integration/slackintegration_confirm_delete.html': 'SlackIntegrationDelete',
    'issue/issue_global_view.html': 'Issue_Global_View',
    'issue/issue_project_list.html': 'Issue_Project_List',
    'issue/issue_create_view.html': 'Issue_Create_View',
    'sprint/sprint_edit.html': 'Sprint_Edit_View',
    'backlog/backlog_list.html': 'Backlog_List',
    'sprint/sprint_confirm_delete.html': 'Sprint_Delete_View',
    'issue/issue_detail_view.html': 'Issue_Detail_View',
    'issue/issue_edit.html': 'Issue_Edit_View',
    'comment/comment_create_view.html': 'Issue_Add_Comment_View',
    'comment/comment_edit_view.html': 'Issue_Edit_Comment_View',
    'attachment/attachment_add_view.html': 'Issue_Add_Attachment_View',
    'timelog/timelog_list_perissue.html': 'Timelog_PerIssue_View',
    'timelog/timelog_create.html': 'Timelog_Create_View',
    'timelog/timelog_form.html': 'Timelog_Edit_View',
    'timelog/timelog_confirm_delete.html': 'Timelog_Delete_View',
    'tag/tag_manage.html': 'TagView',
    'timelog/timelog_list_peruser.html': 'Timelog_PerUser_View',
    'timelog/timelog_d3.html': 'Timelog_d3',
    'timelog/timelog_activity.html': 'Timelog_getActivityData',
    'user_profile/user_profile_page.html': 'ShowProfilePage',
    'user_profile/edit_user_profile.html': 'EditProfilePage',
    'landing_page/home.html': 'Home',
    'registration/password_reset_form.html': 'password_reset',
    'registration/password_reset_complete.html': 'password_reset_complete',
    'timelog_navi.html': "Timelog Tabs",
    'projectnavi.html': "Project Tabs",
    'navigation.html': "Navigation",

}


class Link():
    def __init__(self, template, pattern, params, method):
        self.pattern = pattern
        self.args = []
        self.kwargs = {}
        params = params.split()
        for s in params:
            s = s.split("=")
            if len(s) == 1:
                self.args.append("0")
            else:
                self.kwargs[s[0]] = "0"
        self.template = template
        self.method = "get"
        if method == "post":
            self.method = "post"

    def __str__(self):
        return str(self.pattern)


class Command(BaseCommand):

    help = "Generate a graph of your links."

    def handle(self, *args, **options):
        from django.conf import settings

        root_urlconf = __import__(settings.ROOT_URLCONF)
        all_urlpatterns = root_urlconf.urls.urlpatterns

        views = []

        def get_all_view_names(urlpatterns):
            for pattern in urlpatterns:
                if isinstance(pattern, RegexURLResolver):
                    get_all_view_names(pattern.url_patterns)
                elif isinstance(pattern, RegexURLPattern):
                    if hasattr(pattern.callback, "view_class"):
                        views.append(pattern.callback.view_class)
            return views

        for view in views:
            if hasattr(view, "template_name") and view.template_name:
                print(view.template_name, ":", view.__name__)
            else:
                try:
                    v = view()
                    v.object = "foo"
                    v.object_list = ["foo"]
                    print(v.get_template_names()[0], ":", view.__name__)
                except Exception as e:
                    print(view.__name__, "Err-------------------or:", e)

        links = []
        templates = glob('*/templates/*/*.html')
        templates += glob('*/templates/*.html')
        regex = re.compile(r'''.*(href|post).*{% ?url (?P<quote>['"])(.*?)(?P=quote)(.*?)%}''')
        for t in templates:
            with open(t, 'r') as f:
                content = f.read()
                t = '/'.join(t.split('/')[2:])
                links.extend([
                    Link(t, pattern, params.strip(), method)
                    for (method, quotes, pattern, params)
                    in regex.findall(content)
                ])
        dot = Digraph()
        for link in links:
            try:
                from_node = template_to_view[link.template]
            except KeyError:
                print(link.template)
                from_node = "Unknown"
            url = reverse(link.pattern, args=link.args, kwargs=link.kwargs)
            to_node = resolve(url).func.__name__
            dot.node(from_node, from_node)
            dot.node(to_node, to_node)
            if link.method == "post":
                dot.edge(from_node, to_node, color="lightgrey")
            else:
                dot.edge(from_node, to_node)
        dot.render("linkgraph.gv")
