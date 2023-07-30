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
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect

from issue.models import Issue
from lib.custom_model import get_r_object_or_404
from sprint.forms import SprintForm
from project.models import Project
from sprint.models import Sprint
from event import signals

from urllib.parse import urlparse
import re
from issue.views import process_order_by

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


class NewSprintView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, *args, **kwargs):
        new_sprint = Sprint(project=Project.objects.get(name_short=self.kwargs.get('project')))
        new_sprint.save()
        s = new_sprint.seqnum
        return redirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project'),
                                                           'sqn_s': s
                                                           }))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


class StartSprintView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, *args, **kwargs):
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        if proj.has_active_sprint():
            messages.add_message(request, messages.ERROR, _('Only one current sprint is allowed at once, ' +
                                                            'please finish your current running sprint first.'))
            return redirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project'),
                                                               'sqn_s': self.kwargs.get('sqn_s')
                                                               }))
        relsprint = Sprint.objects.get(project__name_short=self.kwargs.get('project'),
                                       seqnum=self.kwargs.get('sqn_s')
                                       )
        relsprint.set_active()
        proj.currentsprint = relsprint
        proj.save()
        signals.start.send(sender=relsprint.__class__, instance=relsprint, user=self.request.user)
        return redirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project'),
                                                           'sqn_s': self.kwargs.get('sqn_s')
                                                           }))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Sprint, project__name_short=self.kwargs.get('project'),
                                   seqnum=self.kwargs.get('sqn_s')).project.user_has_read_permissions(self.request.user)


class StopSprintView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "sprint/sprint_finish.html"
    breadcrumb = _l("Finish sprint")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proj = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        sprint = get_r_object_or_404(self.request.user, Sprint, project__name_short=self.kwargs.get('project'),
                                     seqnum=self.kwargs.get('sqn_s'))
        context['project'] = proj
        context['sprint'] = sprint
        return context

    def post(self, request, *args, **kwargs):
        proj = Project.objects.get(name_short=self.kwargs.get('project'))
        sprint = Sprint.objects.filter(project__name_short=self.kwargs.get('project')) \
            .get(seqnum=self.kwargs.get('sqn_s'))
        sprint.set_inactive()
        signals.stop.send(sender=sprint.__class__, instance=sprint, user=self.request.user)

        new_sprint = request.POST.get('sprint')
        if not new_sprint:
            return redirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project')}))

        selection = request.POST.getlist('move_to_new_sprint')
        sprint = None
        if new_sprint == 'new':
            if selection:
                sprint = Sprint(project=proj)
                sprint.save()
        else:
            sprint = get_r_object_or_404(self.request.user, Sprint, project=proj, seqnum=new_sprint)

        for issue in proj.issue.filter(number__in=selection):
            issue.sprint = sprint
            issue.save()

        if selection:
            return redirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project'),
                                                               'sqn_s': sprint.seqnum
                                                               }))
        return redirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project')}))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Sprint, project__name_short=self.kwargs.get('project'),
                                   seqnum=self.kwargs.get('sqn_s')).project.user_has_read_permissions(self.request.user)


class SprintEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sprint
    template_name = 'sprint/sprint_edit.html'
    context_object_name = 'sprint'
    form_class = SprintForm

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

    def get_object(self):
        return get_r_object_or_404(self.request.user, Sprint, project__name_short=self.kwargs.get('project'),
                                   seqnum=self.kwargs.get('sqn_s'))


class SprintboardView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'sprint/sprintboard.html'
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
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))

    def get_breadcrumb(self, *args, **kwargs):
        return kwargs['project']


class ToggleIssueToFromSprintView(LoginRequiredMixin, UserPassesTestMixin, View):

    def post(self, request, *args, **kwargs):
        proj = Project.objects.get(name_short=self.kwargs.get('project'))
        relissue = get_r_object_or_404(self.request.user, Issue,
                                       project__name_short=self.kwargs.get('project'),
                                       number=self.request.POST.get('sqn_i')
                                       )
        # this should make this situation TOCTOU-safe
        # in case it doesn't try to use select_for_update()
        try:
            with transaction.atomic():
                if relissue.sprint:
                    sqn_s = relissue.sprint.seqnum
                    relissue.sprint = None
                    relissue.save()
                    return HttpResponseRedirect(reverse('backlog:backlog',
                                                        kwargs={'project': self.kwargs.get('project'), 'sqn_s': sqn_s}))
        except IntegrityError as e:
            raise e

        ref = self.request.META.get('HTTP_REFERER')
        # catch post requests which are not from backlog
        if "backlog" not in ref:
            return HttpResponseRedirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project')}))

        o = urlparse(ref)
        o = o.path.split('/')[-1]
        if re.fullmatch("[0-9]+", o):
            sqn_s = int(o)
            sprint = Sprint.objects.get(project__name_short=self.kwargs.get('project'),
                                        seqnum=sqn_s)
        else:
            sprint = proj.sprint.get_current_sprints().first()
            if not sprint:
                sprint = proj.sprint.get_new_sprints().first()
            # at least during testing this case is possible if there is no new sprint
            if not sprint:
                return HttpResponseRedirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project')}))
            sqn_s = sprint.seqnum

        # this should make this situation TOCTOU-safe
        # in case it doesn't try to use select_for_update()
        try:
            with transaction.atomic():
                if sprint.enddate is None:
                    relissue.sprint = sprint
                    relissue.save()
        except IntegrityError as e:
            raise e
        return HttpResponseRedirect(reverse('backlog:backlog', kwargs={'project': self.kwargs.get('project'),
                                                                       'sqn_s': sqn_s}))

    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
