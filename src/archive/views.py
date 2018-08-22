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
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage

from itertools import chain
from lib.custom_model import get_r_object_or_404
from issue.models import Issue
from project.models import Project

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


class ArchivedIssuesView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'archive/archived_issues_view.html'
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
