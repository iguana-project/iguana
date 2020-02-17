"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.http import Http404
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
import shutil
import os

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from .models import Repository
from .forms import RepositoryCreateForm, RepositoryEditForm
from project.models import Project
from .frontend import Frontend

from django.utils.translation import ugettext as _, ugettext_lazy as _l

# TODO BUG those ssh-files stored on the server needs to be closed


# Create your views here.
class RepositoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Repository
    template_name = 'repository/repository_list.html'
    context_object_name = 'repositories'
    breadcrumb = _l("")

    def get_queryset(self):
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project'),
                                   ).repos.all()

    def test_func(self):
        # allow access for managers and developers
        return get_r_object_or_404(self.request.user, Project,
                                   name_short=self.kwargs.get('project'),
                                   ).developer_allowed(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(RepositoryListView, self).get_context_data(**kwargs)
        context['project'] = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        return context


class RepositoryDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Repository
    template_name = 'repository/repository_detail.html'
    context_object_name = 'repository'
    breadcrumb = _("Repository link's details")

    def get_object(self):
        return get_r_object_or_404(self.request.user, Repository,
                                   project__name_short=self.kwargs.get('project'),
                                   pk=self.kwargs.get('repository'),
                                   )

    def test_func(self):
        # allow access for managers and developers
        try:
            get_r_object_or_404(self.request.user, Repository,
                                project__name_short=self.kwargs.get('project'),
                                pk=self.kwargs.get('repository'),
                                )
        except Http404:
            return 0
        return 1


class RepositoryEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Repository
    form_class = RepositoryEditForm
    template_name = 'repository/repository_edit.html'
    context_object_name = 'repository'
    breadcrumb = _("Edit")

    def get_object(self):
        return get_w_object_or_404(self.request.user, Repository,
                                   project__name_short=self.kwargs.get('project'),
                                   pk=self.kwargs.get('repository'),
                                   )

    def test_func(self):
        # allow access only for managers
        try:
            repo = get_w_object_or_404(self.request.user, Repository,
                                       project__name_short=self.kwargs.get('project'),
                                       pk=self.kwargs.get('repository'),
                                       )
        except Http404:
            return 0
        return 1

    def get_success_url(self):
        return reverse('project:detail', kwargs={'project': self.kwargs.get('project')})


class RepositoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Repository
    form_class = RepositoryCreateForm
    template_name = 'repository/repository_create.html'
    context_object_name = 'repository'
    breadcrumb = _("Create repository link")

    def form_valid(self, form):
        # set project for repository link
        form.instance.project = get_r_object_or_404(self.request.user, Project,
                                                    name_short=self.kwargs.get('project'),
                                                    )
        form.save()
        return super(RepositoryCreateView, self).form_valid(form)

    def test_func(self):
        # allow access only for managers
        try:
            project = get_w_object_or_404(self.request.user, Project,
                                          name_short=self.kwargs.get('project'),
                                          )
        except Http404:
            return 0
        return 1

    def get_success_url(self):
        return reverse('project:detail', kwargs={'project': self.kwargs.get('project')})


class RepositoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Repository
    template_name = 'confirm_delete.html'
    breadcrumb = _l('Delete')

    def get_object(self):
        return get_w_object_or_404(self.request.user, Repository,
                                   project__name_short=self.kwargs.get('project'),
                                   pk=self.kwargs.get('repository'),
                                   )

    def test_func(self):
        # allow access only for managers
        try:
            get_w_object_or_404(self.request.user, Project,
                                name_short=self.kwargs.get('project'),
                                )
        except Http404:
            return 0
        return 1

    def delete(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            repo = self.get_object()
            # delete repo, private and public key
            shutil.rmtree(repo.get_local_repo_path(), ignore_errors=True)
            os.remove(repo.rsa_priv_path.path)
            os.remove(repo.rsa_pub_path.path)

            repo.delete()

        # also in case of "keep_repository"
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('project:edit', kwargs={'project': self.kwargs.get('project')})


# TODO this view is included in issue.url which is not consistent
class FileDiffView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'commit/file_diff.html'
    breadcrumb = _l('File diff')

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def test_func(self):
        # allow access for managers and developers
        try:
            repo = get_r_object_or_404(self.request.user, Project,
                                       name_short=self.kwargs.get('project')
                                       )
        except Http404:
            return 0
        return 1

    def get_context_data(self, **kwargs):
        context = super(FileDiffView, self).get_context_data(**kwargs)

        repo = get_r_object_or_404(self.request.user, Repository,
                                   pk=self.request.POST.get('repository'),
                                   )
        diff = Frontend.get_diff(repository=repo,
                                 sha_commit=self.request.POST.get('commit_sha'),
                                 filepath=self.request.POST.get('filename')
                                 )
        # we supply the diff line by line to do fancy styling in template
        context['diff'] = diff.splitlines()
        context['filename'] = self.request.POST.get('filename')
        context['commit_sha'] = self.request.POST.get('commit_sha')

        return context
