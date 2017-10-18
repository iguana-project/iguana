"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views import View
from django.urls import reverse, reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.views.generic import TemplateView
from django.template.defaulttags import register
from django.template.response import TemplateResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from collections import defaultdict

from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from search.frontend import SearchFrontend
from search.models import Search
from search.forms import SearchEditForm
from project.models import Project
# elements to show for help
from search.frontend import app_list, searchable_fields
from search.parser import comparatorToQExpression as comp_expressions

from django.utils.translation import ugettext as _, ugettext_lazy as _l


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'search/search.html'
    breadcrumb = _("Search")


class AdvancedSearchView(LoginRequiredMixin, View):
    model = Search
    template_name = 'search/advanced_search_list.html'
    breadcrumb = _("Edit searches")

    def get(self, request):
        return TemplateResponse(request,
                                self.template_name,
                                {'npsearches': Search.objects.filter(creator=self.request.user, persistent=False),
                                 'psearches': Search.objects.filter(creator=self.request.user, persistent=True)
                                 })


class ProjectFilterView(LoginRequiredMixin, UserPassesTestMixin, View):
    model = Search
    template_name = 'search/project_filter_list.html'
    breadcrumb = _l("")

    def get(self, request, *args, **kwargs):
        project = get_r_object_or_404(self.request.user, Project,
                                      name_short=self.kwargs.get('project'),
                                      )
        return TemplateResponse(request,
                                self.template_name,
                                {'searches': project.searches.all(),
                                 'project': project,
                                 })

    def test_func(self):
        try:
            project = get_r_object_or_404(self.request.user, Project,
                                          name_short=self.kwargs.get('project'),
                                          )
        except:
            return 0
        return 1


class SearchEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Search
    context_object_name = 'search'
    template_name = 'search/search_edit.html'
    form_class = SearchEditForm
    breadcrumb = _l("Edit")
    success_url = reverse_lazy('search:advanced')

    def test_func(self):
        try:
            get_w_object_or_404(self.request.user, Search,
                                pk=self.kwargs.get('sqn_sh')).creator == self.request.user
        except:
            return 0
        return 1

    def get_object(self):
        return get_w_object_or_404(self.request.user, Search,
                                   pk=self.kwargs.get('sqn_sh'))


class ResultView(LoginRequiredMixin, View):
    template_name = 'search/result_view.html'
    hide_breadcrumbs = True

    def get(self, request):
        return TemplateResponse(request, self.template_name, {'qresult': [], 'searchable_fields': searchable_fields,
                                                              'compare': comp_expressions})

    def post(self, request, *args, **kwargs):
        # result consists of a list of information about discovered objects:
        # [title, link]
        try:
            result = SearchFrontend.query(request.POST['expression'], self.request.user)
        except:
            # this can happen when less than three chars were given to fullext search
            messages.add_message(request, messages.ERROR, _('Please search for at least three characters'))
            result = []

        # prepare set of types contained in search result
        typeset = defaultdict(lambda: 0)
        for title, url, model in result:
            typeset[model] += 1

        # filter result list by object if necessary
        filterobj = ""
        if 'filterobj' in request.POST:
            filterobj = request.POST['filterobj']
            result = [x for x in result if x[2] == filterobj]

        return TemplateResponse(request,
                                self.template_name,
                                {'qresult': result,
                                 'typeset': sorted(typeset.items()),
                                 'qstring': request.POST['expression'],
                                 'filterobj': filterobj,
                                 'searchable_fields': searchable_fields,
                                 'compare': comp_expressions
                                 })


class MakeSearchPersistentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        search = get_w_object_or_404(self.request.user, Search,
                                     creator=self.request.user,
                                     pk=self.request.POST.get('pk'),
                                     persistent=False)
        search.persistent = True
        search.save()

        return redirect(reverse('search:advanced'))

    def test_func(self):
        try:
            search = get_w_object_or_404(self.request.user, Search,
                                         creator=self.request.user,
                                         pk=self.request.POST.get('pk'))
        except:
            return 0
        return 1


class DelSearchPersistentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        search = get_w_object_or_404(self.request.user, Search,
                                     creator=self.request.user,
                                     pk=self.request.POST.get('pk'),
                                     persistent=True)
        search.delete()

        return redirect(reverse('search:advanced'))

    def test_func(self):
        try:
            search = get_w_object_or_404(self.request.user, Search,
                                         creator=self.request.user,
                                         pk=self.request.POST.get('pk'))
        except:
            return 0
        return 1


@register.filter
def get_searchable_items_for_app(apps, app):
    return apps.get(app)
