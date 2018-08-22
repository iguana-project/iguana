"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from lib.custom_model import get_r_object_or_404
from project.models import Project
from sprint.models import Sprint
from issue.views import process_order_by

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


class BacklogListView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'backlog/backlog_list.html'
    context_object_name = 'project'
    breadcrumb = _l("")

    def get_context_data(self, **kwargs):
        context = super(BacklogListView, self).get_context_data(**kwargs)

        # pass olea request to template if present in session object
        context['oleaexpression'] = ''
        if 'oleaexpression' in self.request.session:
            context['oleaexpression'] = self.request.session['oleaexpression']
            del self.request.session['oleaexpression']

        # focus olea bar if present in session object
        context['oleafocus'] = ''
        if 'oleafocus' in self.request.session:
            context['oleafocus'] = self.request.session['oleafocus']
            del self.request.session['oleafocus']

        storypoints = False
        user_points = {}
        issues = self.get_sprint_issues()
        sp_total = 0
        for issue in issues.filter(storypoints__gt=0):
            sp_total += issue.storypoints
            points_per_user = issue.assignee.all().count()
            for user in issue.assignee.all():
                if user.username in user_points:
                    user_points[user.username] += round(issue.storypoints/points_per_user, 1)
                else:
                    user_points[user.username] = round(issue.storypoints/points_per_user, 1)
        context['storypoints'] = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
        context['storypoints_total'] = sp_total
        return context

    def get_object(self):
        return Project.objects.get(name_short=self.kwargs.get('project'))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)

    def get_sqn_s(self):
        if self.kwargs.get('sqn_s') and get_r_object_or_404(self.request.user, Sprint,
                                                            project__name_short=self.kwargs.get('project'),
                                                            seqnum=self.kwargs.get('sqn_s')):
            return int(self.kwargs.get('sqn_s'))
        else:
            proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
            current = proj.sprint.get_current_sprints()
            if len(current) > 0:
                return int(current[0].seqnum)
            else:
                planned = proj.sprint.get_new_sprints()
                if len(planned) > 0:
                    return int(planned[0].seqnum)
                else:
                    return -1

    def is_sprint_current(self):
        sqn_s = self.get_sqn_s()
        return (
                Sprint.objects.filter(seqnum=sqn_s)
                .get(project__name_short=self.kwargs.get('project'))
                .is_active()
               )

    def is_old_sprint(self):
        sqn_s = self.get_sqn_s()
        return (
                Sprint.objects.filter(seqnum=sqn_s)
                .get(project__name_short=self.kwargs.get('project'))
                .is_inactive()
               )

    def _filter_issues(self, issues):
        my_issues = self.request.GET.get('myissues', 'false')
        if my_issues == 'true':
            issues = issues.filter(assignee=self.request.user)

        issues = process_order_by(self.request, issues)
        return issues

    def get_sprint_issues(self):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        issues = proj.issue.filter(sprint__seqnum=self.get_sqn_s()).not_archived()
        return self._filter_issues(issues)

    def get_sprint_issues_left(self):
        sprint = get_r_object_or_404(self.request.user, Sprint,
                                     project__name_short=self.kwargs['project'], seqnum=self.get_sqn_s())
        return sprint.issues_left()

    def get_backlog_issues(self):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        issues = proj.issue.without_sprint().not_archived()
        return self._filter_issues(issues)
