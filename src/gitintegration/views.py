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
        return get_r_object_or_404(self.request.user, Repository,
                                   project__name_short=self.kwargs.get('project'),
                                   pk=self.kwargs.get('repository'),
                                   )


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
        # allow access only for managers (write access)
        return get_w_object_or_404(self.request.user, Repository,
                                   project__name_short=self.kwargs.get('project'),
                                   pk=self.kwargs.get('repository'),
                                   )

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
        # allow access only for managers (write access)
        return get_w_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

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
        # allow access only for managers (write access)
        return get_w_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

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
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

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
