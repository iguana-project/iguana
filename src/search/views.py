"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from django.http import Http404
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
from search.fieldcheckings import NOT_PROJ_RELATED
from search.frontend import app_list, searchable_fields
from search.parser import comparatorToQExpression as comp_expressions

from django.utils.translation import ugettext as _, ugettext_lazy as _l

FILTER_PROJ = 'filterproj'
FILTER_TYPE = 'filtertype'


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
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


class SearchEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Search
    context_object_name = 'search'
    template_name = 'search/search_edit.html'
    form_class = SearchEditForm
    breadcrumb = _l("Edit")
    success_url = reverse_lazy('search:advanced')

    def test_func(self):
        return get_w_object_or_404(self.request.user, Search, pk=self.kwargs.get('sqn_sh'))

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
        except ValueError:
            # this can happen when less than three chars were given to full text search
            messages.add_message(request, messages.ERROR, _('Please search for at least three characters'))
            result = []

        # prepare set of types contained in search result
        # with/-out project filter
        typeset = defaultdict(lambda: [0, 0])
        # with/-out type filter
        projects = defaultdict(lambda: [0, 0])
        # with/-out type filter
        not_proj_related = defaultdict(lambda: [0, 0])
        for title, url, model, rel_project in result:
            typeset[model][1] += 1
            if FILTER_PROJ not in request.POST or rel_project == request.POST[FILTER_PROJ]:
                typeset[model][0] += 1
            # amount for this project with active type filter
            if _(NOT_PROJ_RELATED) == rel_project:
                not_proj_related[rel_project][1] += 1
                # amount for this project with active type filter
                if FILTER_TYPE not in request.POST or model == request.POST[FILTER_TYPE]:
                    not_proj_related[rel_project][0] += 1
            else:
                projects[rel_project][1] += 1
                # amount for this project with active type filter
                if FILTER_TYPE not in request.POST or model == request.POST[FILTER_TYPE]:
                    projects[rel_project][0] += 1

        # filter result list by object if necessary
        filtertype = ""
        if FILTER_TYPE in request.POST:
            filtertype = request.POST[FILTER_TYPE]
            result = [x for x in result if x[2] == filtertype]

        filterproj = ""
        if FILTER_PROJ in request.POST:
            filterproj = request.POST[FILTER_PROJ]
            result = [x for x in result if x[3] == filterproj]

        return TemplateResponse(request,
                                self.template_name,
                                {'qresult': result,
                                 'typeset': sorted(typeset.items()),
                                 # append the NOT_PROJ_RELATED entry always to the end
                                 'projects': sorted(projects.items())+list(not_proj_related.items()),
                                 'qstring': request.POST['expression'],
                                 FILTER_TYPE: filtertype,
                                 FILTER_PROJ: filterproj,
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
        return get_w_object_or_404(self.request.user, Search, creator=self.request.user, pk=self.request.POST.get('pk'))


class DelSearchPersistentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        search = get_w_object_or_404(self.request.user, Search,
                                     creator=self.request.user,
                                     pk=self.request.POST.get('pk'),
                                     persistent=True)
        search.delete()

        return redirect(reverse('search:advanced'))

    def test_func(self):
        return get_w_object_or_404(self.request.user, Search, creator=self.request.user, pk=self.request.POST.get('pk'))


@register.filter
def get_searchable_items_for_app(apps, app):
    return apps.get(app)
