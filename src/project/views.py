"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import serializers
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from landing_page.actstream_util import follow_project, unfollow_project

from datetime import timedelta
import json

from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from .forms import ProjectCreateForm, ProjectEditForm, clear_assignee_follow_m2m_fields_for_users
from .models import Project
from integration.models import SlackIntegration
from kanbancol.models import KanbanColumn
from timelog.models import Timelog
from common.settings import HOST, SLACK_ID
from landing_page.actstream_util import unfollow_project

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


class ProjectListAllView(LoginRequiredMixin, ListView):
    template_name = 'project_list.html'
    context_object_name = 'latest_project_list'
    breadcrumb = _l("Projects")
    hide_breadcrumbs = True

    def get_context_data(self, **kwargs):
        context = super(ProjectListAllView, self).get_context_data(**kwargs)
        if self.request.GET.get('data') is not None:
            self.request.user.set_preference('project_list_chart_type', self.request.GET.get('data'))
        data = self.request.user.get_preference('project_list_chart_type', default="timelog")
        context['chart_type'] = data
        return context

    def get_queryset(self):
        return Project.objects.filter(Q(manager=self.request.user) |
                                      Q(developer=self.request.user)
                                      ).distinct().order_by('-created_at')[:10]


# shows timelog for all user of this project
class ProjectDetailTimelogView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_timelog.html'
    breadcrumb = _l("")

    def dispatch(self, request, *args, **kwargs):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        if not request.user.is_authenticated:
            return super(ProjectDetailTimelogView, self).dispatch(request, *args, **kwargs)
        elif proj.activity_only_for_managers and not proj.is_manager(self.request.user):
            return HttpResponseRedirect(reverse_lazy('project:usertimelog',
                                        kwargs={'project': proj.name_short, 'username': self.request.user.username}
                                        ))
        return super(ProjectDetailTimelogView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailTimelogView, self).get_context_data(**kwargs)
        context['project'] = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        devs = context['project'].get_members()
        context['logs'] = []
        devs = serializers.serialize("json", devs, fields=('username'))
        devs = json.loads(devs)

        for dev in devs:
            logs = Timelog.objects.filter(user=dev['pk'], issue__project=context['project']).order_by('-created_at')
            total_time = timedelta(0)
            for l in logs:
                total_time += l.time
            dev['fields']['total'] = total_time
            dev['fields']['logs'] = logs[:5]
            dev['fields']['ava_url'] = context['project'].get_members().filter(
                                                                           username=dev['fields']['username']
                                                                           ).first().avatar.url

        context['developer'] = sorted(devs, key=lambda dev: dev['fields']['total'], reverse=True)
        return context

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


class ProjectUserTimelogView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'project/project_timelog_detail.html'
    breadcrumb = _l("")

    def dispatch(self, request, *args, **kwargs):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        if not request.user.is_authenticated:
            return super(ProjectUserTimelogView, self).dispatch(request, *args, **kwargs)
        elif (proj.activity_only_for_managers and not proj.is_manager(request.user) and
              request.user.username != self.kwargs.get('username')):
            return HttpResponseRedirect(reverse_lazy('project:usertimelog',
                                        kwargs={'project': proj.name_short, 'username': self.request.user.username}
                                        ))
        return super(ProjectUserTimelogView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectUserTimelogView, self).get_context_data(**kwargs)
        context['project'] = Project.objects.get(name_short=self.kwargs.get('project'))
        logs = Timelog.objects.filter(user__username=kwargs['username'],
                                      issue__project=context['project']
                                      ).order_by('-created_at')
        dev = context['project'].get_members().filter(username=self.kwargs.get('username'))
        if dev.count() != 1:
            raise Http404
        paginator = Paginator(logs, 20)
        page = self.request.GET.get('page')
        try:
            logs = paginator.page(page)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            logs = paginator.page(paginator.num_pages)
        context['logs'] = logs

        context['ava_url'] = dev.first().avatar.url
        context['user'] = kwargs['username']
        return context

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'project/project_detail.html'
    context_object_name = 'project'
    slug_field = 'name_short'
    slug_url_kwarg = 'project'
    breadcrumb = ""

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        if self.request.GET.get('data') is not None:
            self.request.user.set_preference('project_detail_chart_type_'+self.get_queryset().first().name_short,
                                             self.request.GET.get('data'))
        data = self.request.user.get_preference('project_detail_chart_type_'+self.get_queryset().first().name_short,
                                                default="timelog")
        context['chart_type'] = data
        return context

    def get_queryset(self):
        return Project.objects.filter(name_short=self.kwargs.get('project'))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

    def get(self, request, *args, **kwargs):
        response = DetailView.get(self, request, *args, **kwargs)

        # check if the follow button was hit
        if request.GET.get("follow", "") == "true":
            follow_project(request.user, self.object)
        # check if the unfollow button was hit
        if request.GET.get("follow", "") == "false":
            unfollow_project(request.user, self.object)

        return response


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'project/project_create.html'
    form_class = ProjectCreateForm
    slug_field = 'name_short'
    slug_url_kwarg = 'project'
    breadcrumb = _l("New")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        # NOTE: this is necessary here even though it is a CreateView, because
        #       "ValueError: "<Project: test_project>" needs to have a value for
        #       field "project" before this many-to-many relationship can be used."
        form.instance.save()
        form.instance.manager.add(self.request.user)

        # per default a user follows the project he created
        follow_project(self.request.user, form.instance)
        # and every developer follows the project, too
        for dev in form.cleaned_data["developer"]:
            follow_project(dev, form.instance)
        return super(ProjectCreateView, self).form_valid(form)


class ProjectEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    context_object_name = 'project'
    form_class = ProjectEditForm
    template_name = 'project/project_edit.html'
    slug_field = 'name_short'
    slug_url_kwarg = 'project'
    breadcrumb = ""

    def test_func(self):
        return get_w_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

    def get_context_data(self, **kwargs):
        context = super(ProjectEditView, self).get_context_data(**kwargs)
        context['integration_slack'] = SlackIntegration.objects.filter(project__name_short=self.kwargs['project'])
        context['slack_id'] = SLACK_ID
        context['columns'] = KanbanColumn.objects.filter(project__name_short=self.kwargs['project'])
        context['host'] = HOST
        return context

    def form_valid(self, form):
        # check if manager or developers have changed
        for changed in form.changed_data:
            if changed == "developer":
                # newly added developers follow the project by default, unfollow in forms.py
                for dev in set(form.cleaned_data[changed]) - set(self.object.developer.all()):
                    follow_project(dev, form.instance)
            if changed == "manager":
                # newly added managers follow the project by default, unfollow in forms.py
                for man in set(form.cleaned_data[changed]) - set(self.object.manager.all()):
                    follow_project(man, form.instance)

        return UpdateView.form_valid(self, form)


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('project:list')
    slug_field = 'name_short'
    slug_url_kwarg = 'project'
    breadcrumb = _l("Delete")
    template_name = 'confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            # clean up before delete
            clear_assignee_follow_m2m_fields_for_users(self.get_object().get_members(), self.get_object())
            self.get_object().delete()
            return HttpResponseRedirect(self.success_url)

        # in case of "keep_project" we redirect to the settings page and not to the list of projects
        return HttpResponseRedirect(reverse('project:edit', kwargs={'project': self.kwargs['project']}))

    def test_func(self):
        return get_w_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


class LeaveProjectView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('project:list')
    slug_field = 'name_short'
    slug_url_kwarg = 'project'
    breadcrumb = _l("Leave")
    template_name = 'confirm_leave.html'

    def delete(self, request, *args, **kwargs):
        if ('delete' in request.POST and
                (self.get_object().manager.count() > 1 or self.request.user not in self.get_object().manager.all())):
            self.get_object().manager.remove(self.request.user)
            self.get_object().developer.remove(self.request.user)
            clear_assignee_follow_m2m_fields_for_users([self.request.user], self.get_object())
            return HttpResponseRedirect(self.success_url)
        elif 'keep' in request.POST:
            return HttpResponseRedirect(reverse('project:detail', kwargs={'project': self.kwargs['project']}))

        messages.add_message(request,
                             messages.INFO,
                             _("""You can't leave the project. You are the last manager.
                                  Instead you can delete it here, if you want that."""
                               )
                             )
        return HttpResponseRedirect(reverse('project:edit', kwargs={'project': self.kwargs['project']}))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
