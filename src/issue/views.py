"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.db.models import Q

from itertools import chain
from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from lib.show_more_mixin import ShowMoreMixin
from sendfile import sendfile
from .forms import LimitKanbanForm, CommentForm, AttachmentForm
from .models import Issue, Comment, Attachment
from kanbancol.models import KanbanColumn
from project.models import Project
from sprint.models import Sprint
from event import signals
from issue import parser

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l
from lib.multiform import MultiFormsView
from timelog.forms import TimelogCreateForm
from django.utils import timezone
import os


def process_order_by(request, issues):
    # transfer order_by and reverse GET parameter to session object
    if request.GET.get('order_by') is not None:
        request.session['order_by'] = request.GET.get('order_by')
    if request.GET.get('reverse') is not None:
        request.session['reverse'] = request.GET.get('reverse')

    order_type = request.session.get('order_by', 'number')
    reverse = request.session.get('reverse', 'false')
    if order_type in ('number', 'title', 'type', 'kanbancol'):
        if reverse == 'true':
            issues = issues.order_by('-'+order_type, 'number')
        else:
            issues = issues.order_by(order_type, 'number')
    elif order_type in ('priority', 'storypoints'):
        if reverse == 'true':
            issues = issues.order_by(order_type, 'number')
        else:
            issues = issues.order_by('-'+order_type, 'number')
    return issues


class IssueGlobalView(LoginRequiredMixin, TemplateView):
    template_name = 'issue/issue_global_view.html'
    hide_breadcrumbs = True
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(IssueGlobalView, self).get_context_data(**kwargs)

        proj = self.request.GET.get('project', None)
        show_done = self.request.GET.get('show_done', 'false')
        sprint_only = self.request.GET.get('sprint_only', 'false')
        followed = self.request.GET.get('followed', 'false')
        show_archived = self.request.GET.get('show_archived', 'false')
        issues = Issue.objects.filter(Q(participant=self.request.user) | Q(assignee=self.request.user)).distinct()
        if proj:
            project = Project.objects.filter(name_short=proj)
            if project.exists():
                issues = issues.filter(project=project.first())
        if show_done == 'false':
            issues = issues.exclude(kanbancol__type='Done')
        if followed == 'true':
            issues = issues.filter(participant=self.request.user)
        else:
            issues = issues.filter(assignee=self.request.user)
        if show_archived != 'true':
            issues = issues.exclude(archived=True)
        if sprint_only == 'true':
            issues = issues.filter(sprint__isnull=False)
            issues = issues.filter(sprint__startdate__isnull=False, sprint__enddate__isnull=True)

        issues = process_order_by(self.request, issues)

        paginator = Paginator(issues, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            issues = paginator.page(page)
        except PageNotAnInteger:
            issues = paginator.page(1)
        except EmptyPage:
            issues = paginator.page(paginator.num_pages)

        context['issues'] = issues
        return context


class SprintboardView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'issue/sprintboard.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super(SprintboardView, self).get_context_data(**kwargs)
        context['nbar'] = 'sprint'
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        context['colwidth'] = int(100/len(proj.kanbancol.all()))

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

        if proj.currentsprint is not None and proj.currentsprint.is_active():
            issuelist = proj.currentsprint.issue.all()
        else:
            issuelist = proj.issue.without_sprint().not_archived()
        myiss = self.request.GET.get('myissues', 'false')
        issuelist_count = issuelist
        if myiss == 'true':
            issuelist_count = issuelist_count.filter(assignee=self.request.user)
        issue_all = issuelist_count.count()
        issue_done = 0
        for issue in issuelist_count:
            if issue.kanbancol.type == 'Done':
                issue_done += 1

        if issue_all == 0:
            context['progress'] = 0
        else:
            context['progress'] = int(100*issue_done/issue_all)
        context['issue_all'] = issue_all
        context['issue_done'] = issue_done

        issues = process_order_by(self.request, issuelist)
        context['issuelist'] = issues

        return context

    def get_object(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)

    def get_breadcrumb(self, *args, **kwargs):
        return kwargs['project']


# olea short for one line edit add - the functionality to add issues in backlog and board
class ProcessOleaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        project = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        try:
            parser.compile(self.request.POST.get('expression'), project, self.request.user)

            # add to sprint if currentsprint is set and issue was newly created
            if self.request.POST.get('currentsprint') != "" and parser.issue_created:
                sprint = Sprint.objects.get(project__name_short=self.kwargs.get('project'),
                                            seqnum=self.request.POST.get('currentsprint'))
                parser.issue_to_change.sprint = sprint
                parser.issue_to_change.save()
        except Exception as e:
            messages.add_message(request, messages.ERROR,
                                 _("An error occurred when processing your request") + ": " + str(e))
            # store expression in session data to give edit ability to user
            self.request.session['oleaexpression'] = self.request.POST.get('expression')

        # set focus to olea bar
        self.request.session['oleafocus'] = 'autofocus'

        return redirect(self.request.POST.get('next'))


class BacklogListView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'issue/backlog_list.html'
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


class AssignIssueToMeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:projList', kwargs={'project': self.kwargs.get('project')})

    def post(self, request, *args, **kwargs):
        relassignee = self.request.user
        relissue = get_r_object_or_404(self.request.user, Issue,
                                       project__name_short=self.kwargs.get('project'),
                                       number=self.request.POST.get('sqn_i')
                                       )
        relissue.assignee.add(relassignee)
        return redirect(self.get_success_url())

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)


class RemoveIssueFromMeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:projList', kwargs={'project': self.kwargs.get('project')})

    def post(self, request, *args, **kwargs):
        user = self.request.user
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=self.kwargs.get('project'),
                                    number=self.request.POST.get('sqn_i')
                                    )
        assignees = issue.assignee.all()

        if (user not in assignees):
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Issue was not in selected sprint, not performing any action')
                                 )
        else:
            issue.assignee.remove(user)

        return redirect(self.get_success_url())

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)


class AddIssueToKanbancolView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url[:-1]
        return reverse('issue:projList', kwargs={'project': self.kwargs.get('project')})

    def post(self, request, *args, **kwargs):
        issue = (
                Issue.objects.filter(project__name_short=self.kwargs.get('project'),
                                     number=self.request.POST.get('sqn_i'))
                )

        kanbancol = KanbanColumn.objects.filter(project__name_short=self.kwargs.get('project'),
                                                position=self.request.POST.get('sqn_k')
                                                )

        if issue.count() != 1 or kanbancol.count() != 1:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Given issue or kanbancol does not exist'),
                                 )
        else:
            issue = issue.first()
            signals.modify.send(sender=Issue,
                                instance=issue,
                                changed_data={'kanbancol': str(kanbancol.first())},
                                user=self.request.user,
                                )
            issue.kanbancol = kanbancol.first()
            issue.save(update_fields=['kanbancol'])

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)


class ArchiveSingleIssueView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:detail', kwargs={'project': self.kwargs.get('project'),
                                               'sqn_i': self.request.POST.get('sqn_i')
                                               })

    def post(self, request, *args, **kwargs):
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=self.kwargs.get('project'),
                                    number=self.request.POST.get('sqn_i')
                                    )
        issue.archived = True
        issue.save()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)


class UnArchiveSingleIssueView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:detail', kwargs={'project': self.kwargs.get('project'),
                                               'sqn_i': self.request.POST.get('sqn_i')
                                               })

    def post(self, request, *args, **kwargs):
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=self.kwargs.get('project'),
                                    number=self.request.POST.get('sqn_i')
                                    )
        issue.archived = False
        issue.kanbancol = issue.project.kanbancol.filter(type='ToDo').first()
        issue.sprint = None
        issue.save()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)


class ArchiveMultipleIssueView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:projList', kwargs={'project': self.kwargs.get('project')})

    def post(self, request, *args, **kwargs):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        issues = Issue.objects.filter(project=proj,
                                      kanbancol__position=self.request.POST.get('pos_c')
                                      ).without_sprint().not_archived()

        if self.request.POST.get('filter') == 'true':
            issues = issues.filter(assignee=self.request.user)

        count = issues.count()
        if count == 0:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('No issues to archive'),
                                 )
        else:
            messages.add_message(request,
                                 messages.ERROR,
                                 str(count) + _(' issues moved to archive'),
                                 )
        for issue in issues:
            issue.archived = True
            issue.save()

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)


class ArchivedIssuesView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'issue/issue_archived_view.html'
    context_object_name = 'project'
    items_per_page_sprints = 5
    items_per_page_nosprint = 5
    item_list = None
    item_list_nosprint = None
    breadcrumb = _l('Archive')

    def get(self, *args, **kwargs):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        self.item_list = proj.sprint.order_by('-seqnum')
        self.item_list_nosprint = Issue.objects.filter(project__name_short=self.kwargs.get('project'),
                                                       archived=True, sprint=None)
        return super(ArchivedIssuesView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArchivedIssuesView, self).get_context_data(**kwargs)
        context['nbar'] = 'sprint'
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        archived_issues_without_sprint = Issue.objects.filter(project__name_short=self.kwargs.get('project'),
                                                              archived=True, sprint=None)
        context['archived_issues_without_sprint'] = archived_issues_without_sprint
        context['sprints_sorted'] = proj.sprint.order_by('-seqnum')
        # paginator sprints
        if self.item_list:
            paginator = Paginator(self.item_list, self.items_per_page_sprints)
            page = self.request.GET.get('page')
            if not page or not page.isdigit():
                items = paginator.page(1)
            else:
                try:
                    items = self.getItemsUntilPage(paginator, page)
                except EmptyPage:
                    items = self.getItemsUntilPage(paginator, paginator.num_pages)
            context['page_items'] = items
        # paginator issues without sprint
        if self.item_list_nosprint:
            paginator_nosprint = Paginator(self.item_list_nosprint, self.items_per_page_nosprint)
            page_nosprint = self.request.GET.get('page_nosprint')
            if not page_nosprint or not page_nosprint.isdigit():
                items_nosprint = paginator_nosprint.page(1)
            else:
                try:
                    items_nosprint = self.getItemsUntilPage(paginator_nosprint, page_nosprint)
                except EmptyPage:
                    items_nosprint = self.getItemsUntilPage(paginator_nosprint, paginator_nosprint.num_pages)
            context['page_items_nosprint'] = items_nosprint
        return context

    def get_object(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)

    def getItemsUntilPage(self, paginator, pageNumber):
        # for more comments see ShowMoreMixin
        items = paginator.page(pageNumber)
        for i in reversed(range(1, int(pageNumber))):
            items.object_list = list(chain(paginator.page(i).object_list, items.object_list))
        return items


class IssueDetailView(LoginRequiredMixin, UserPassesTestMixin, MultiFormsView):
    template_name = 'issue/issue_detail_view.html'
    context_object_name = 'issue'
    form_classes = {
        'comment': CommentForm,
        'attachment': AttachmentForm,
        'attachmentCom': AttachmentForm,
        'timelog': TimelogCreateForm,
    }
    grouped_forms = {
        'commentAtt': ['comment', 'attachmentCom'],
    }

    def get_success_url(self, form_name=None):
        # go back to the issue detail view
        return reverse('issue:detail',
                       kwargs={"project": self.kwargs.get("project"), "sqn_i": self.kwargs.get("sqn_i")})

    def get_object(self):
        return get_r_object_or_404(self.request.user, Issue, project__name_short=self.kwargs.get('project'),
                                   number=self.kwargs.get('sqn_i'))

    def test_func(self):
        get_r_object_or_404(self.request.user, Project,
                            name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)
        return 1

    def get_breadcrumb(self, *args, **kwargs):
        # self has no request and so no user -> we use get_object_or_404
        issue = get_object_or_404(Issue,
                                  project__name_short=kwargs.get('project'), number=kwargs.get('sqn_i')
                                  )
        return issue.get_ticket_identifier()

    def get_context_data(self, *args, **kwargs):
        context = super(IssueDetailView, self).get_context_data(*args, **kwargs)
        context['project'] = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs['project'])
        issue = self.get_object()
        context['issue'] = issue

        # check the order of the comments
        userSetting = self.request.user.get_preference("issue_comment-order", default="oldest")
        requestSetting = self.request.GET.get('order_by')

        if requestSetting == "newest" or\
                (requestSetting is None and userSetting == "newest"):
            # order the comments by the newest
            context['comments'] = issue.comments.order_by('-when').all()
            context['comment_order'] = "newest"
        else:
            # order the comments by the oldest (default in the database)
            context['comments'] = issue.comments.all()
            context['comment_order'] = "oldest"

        # save the setting to the user model
        if userSetting != context['comment_order']:
            self.request.user.set_preference("issue_comment-order", context['comment_order'])

        return context

    def get(self, *args, **kwargs):
        issue = get_r_object_or_404(self.request.user, Issue,
                                    project__name_short=kwargs.get('project'), number=kwargs.get('sqn_i'))
        notification = self.request.user.notifications.filter(issue=issue)
        if notification:
            notification.get().delete()
        return super(IssueDetailView, self).get(*args, **kwargs)

    def commentAtt_form_valid(self, forms, form):
        # get the new comment and attachment object
        newComment = [f for f in form if isinstance(f, CommentForm)][0].save(commit=False)
        newAttachment = [f for f in form if isinstance(f, AttachmentForm)][0].save(commit=False)
        # set additional needed information
        newComment.creator = newAttachment.creator = self.request.user
        newComment.issue = newAttachment.issue = self.get_object()

        # check if a file was added to the comment
        if newAttachment.file.name:
            # save the attachment
            newAttachment.save()
            # link attachment to comment
            newComment.attachment = newAttachment

        # save the comment
        newComment.save()
        signals.create.send(sender=newComment.__class__, instance=newComment, user=newComment.creator)

    def attachment_form_valid(self, forms, form):
        newAttachment = form.save(commit=False)
        newAttachment.creator = self.request.user
        newAttachment.issue = self.get_object()

        newAttachment.save()

        return super(IssueDetailView, self).form_valid(forms, form)

    def timelog_form_valid(self, forms, form):
        newTime = form.save(commit=False)
        newTime.user = self.request.user
        newTime.issue = self.get_object()
        newTime.save()

        return super(IssueDetailView, self).form_valid(forms, form)

    def get_timelog_initial(self):
        return {'created_at': timezone.now()}

    def create_timelog_form(self, **kwargs):
        form = TimelogCreateForm(**kwargs)
        form.fields['created_at'].disabled = True
        return form

    def create_attachmentCom_form(self, **kwargs):
        form = AttachmentForm(**kwargs)
        form.fields['file'].required = False
        return form


class IssueCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Issue
    template_name = 'issue/issue_create_view.html'
    form_class = LimitKanbanForm
    breadcrumb = _l("New Issue")

    def form_valid(self, form):
        form.instance.project = Project.objects.get(name_short=self.kwargs.get('project'))
        form.instance.creator = self.request.user
        # NOTE: this is necessary here even though it is a CreateView, because
        #       otherwise the reversematch in signals.create.send fails
        form.instance.save()
        signals.create.send(sender=self.model, instance=form.instance, user=self.request.user)
        return super(IssueCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(IssueCreateView, self).get_context_data(**kwargs)
        context['project'] = self.kwargs.get('project')
        return context

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs(), proj=self.kwargs.get('project'), issue=None)
        form.fields['kanbancol'].queryset = KanbanColumn.objects.filter(project__name_short=self.kwargs.get('project'))
        form.fields['kanbancol'].initial = KanbanColumn.objects.filter(
                                            project__name_short=self.kwargs.get('project')
                                           ).first()
        project = Project.objects.get(name_short=self.kwargs.get('project'))

        return form

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)

    def get_success_url(self):
        return reverse('issue:backlog', kwargs={'project': self.kwargs['project']})


class IssueDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Issue
    breadcrumb = _("Delete")
    template_name = 'confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            if self.get_object().logs.count() != 0:
                messages.add_message(request, messages.ERROR, _('This issue has logged time, it can\'t be deleted.'))
            else:
                self.get_object().delete()
            return HttpResponseRedirect(self.get_success_url())

        # in case of "keep_issue" we want back to the detail-issue-page instead of backlog
        # (where this issue is not contained anymore, since it have to be in the archive)
        return HttpResponseRedirect(reverse('issue:detail',
                                    kwargs={'project': self.kwargs['project'], 'sqn_i': self.kwargs['sqn_i']}))

    def get_success_url(self):
        return reverse('issue:backlog', kwargs={'project': self.kwargs['project']})

    def test_func(self):
        get_w_object_or_404(self.request.user, Project,
                            name_short=self.kwargs.get('project')).user_has_write_permissions(self.request.user)
        return 1

    def get_object(self):
        return get_r_object_or_404(self.request.user, Issue, project__name_short=self.kwargs.get('project'),
                                   number=self.kwargs.get('sqn_i'))


class IssueEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Issue
    context_object_name = 'Issue'
    template_name = 'issue/issue_edit.html'
    form_class = LimitKanbanForm
    breadcrumb = _l("Edit")

    def form_valid(self, form):
        if form.has_changed():
            old = Issue.objects.get(pk=self.object.pk)
            changed_data = signals.fields_to_changed_data(old, form.changed_data)
            ret = super(IssueEditView, self).form_valid(form)
            signals.modify.send(sender=self.model,
                                instance=form.instance,
                                changed_data=changed_data,
                                user=self.request.user,
                                )
            return ret
        return super(IssueEditView, self).form_valid(form)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs(), proj=self.kwargs.get('project'), issue=self.kwargs.get('sqn_i'))
        form.fields['kanbancol'].queryset = KanbanColumn.objects.filter(project=self.object.project)
        return form

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)

    def get_object(self):
        return get_r_object_or_404(self.request.user, Issue, project__name_short=self.kwargs.get('project'),
                                   number=self.kwargs.get('sqn_i'))


# even manager can edit only their own comments
class IssueEditCommentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    template_name = 'comment/comment_edit.html'
    form_class = CommentForm
    breadcrumb = _l("Edit comment")

    def test_func(self):
        # NOTE: even manager are not allowed to change/delete comments of other users
        return get_r_object_or_404(self.request.user, Comment,
                                   issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'),
                                   seqnum=self.kwargs.get('pk_c')
                                   ).user_has_write_permissions(self.request.user)

    def get_object(self):
        return Comment.objects.get(issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'),
                                   seqnum=self.kwargs.get('pk_c')
                                   )


class IssueDeleteCommentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    breadcrumb = _l("")
    template_name = 'confirm_delete.html'

    def test_func(self):
        return get_r_object_or_404(self.request.user, Comment,
                                   issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'),
                                   seqnum=self.kwargs.get('pk_c')
                                   ).user_has_write_permissions(self.request.user)

    def get_success_url(self):
        # go back to the issue detail view
        return reverse('issue:detail',
                       kwargs={"project": self.kwargs.get("project"), "sqn_i": self.kwargs.get("sqn_i")})

    def get_object(self):
        return Comment.objects.get(issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'),
                                   seqnum=self.kwargs.get('pk_c')
                                   )

    def get(self, request, *args, **kwargs):
        # normally the GET request wants to display a confirmation page
        # to avoid this simply perform the POST request (which actually does the deletion)
        return self.post(request, *args, **kwargs)


# TODO BUG this view might leak some ressources: there is an unclosed file,
#          which has been opened with mode='rb' and closefd=True
class AttachmentDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    form_class = AttachmentForm

    def get(self, request, *args, **kwargs):
        attachment = get_r_object_or_404(self.request.user, Attachment,
                                         issue__project__name_short=self.kwargs.get('project'),
                                         issue__number=self.kwargs.get('sqn_i'),
                                         seqnum=self.kwargs.get('sqn_a'))
        return sendfile(request, attachment.file.path, attachment=False)

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project')).user_has_read_permissions(self.request.user)

    def get_object(self):
        return Attachment.objects.get(issue__project__name_short=self.kwargs.get('project'),
                                      issue__number=self.kwargs.get('sqn_i'),
                                      seqnum=self.kwargs.get('sqn_a'))


class AttachmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Attachment
    breadcrumb = _l("")
    template_name = 'confirm_delete.html'

    def test_func(self):
        return get_r_object_or_404(self.request.user, Attachment,
                                   issue__project__name_short=self.kwargs.get('project'),
                                   issue__number=self.kwargs.get('sqn_i'),
                                   seqnum=self.kwargs.get('sqn_a')
                                   ).user_has_write_permissions(self.request.user)

    def delete(self, request, *args, **kwargs):
        # get the file path to delete it later
        filePath = self.get_object().file.path

        # delete the object from the database
        response = DeleteView.delete(self, request, *args, **kwargs)
        # delete the file from disk
        os.remove(filePath)

        return response

    def get_success_url(self):
        # go back to the issue detail view
        return reverse('issue:detail',
                       kwargs={"project": self.kwargs.get("project"), "sqn_i": self.kwargs.get("sqn_i")})

    def get_object(self):
        return Attachment.objects.get(issue__project__name_short=self.kwargs.get('project'),
                                      issue__number=self.kwargs.get('sqn_i'),
                                      seqnum=self.kwargs.get('sqn_a')
                                      )

    def get(self, request, *args, **kwargs):
        # normally the GET request wants to display a confirmation page
        # to avoid this simply perform the POST request (which actually does the deletion)
        return self.post(request, *args, **kwargs)
