"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse


from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from kanbancol.models import KanbanColumn
from kanbancol.forms import KanbanColumnForm
from project.models import Project
from common.views import BreadcrumbView

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


class KanbanColumnBreadcrumbView(BreadcrumbView):
    """
    Adds an additional breadcrumb of the current Kanban column without a hyperlink.
    """
    # TODO BUG does this need an auth check?
    def get_breadcrumb(self, *args, **kwargs):
        kc = get_object_or_404(KanbanColumn,
                               project__name_short=kwargs['project'], position=kwargs['position'])
        return _('Column') + ' "' + kc.name + '"'


class KanbanColumnCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = KanbanColumn
    template_name = 'kanbancol/create_kanbancolumn.html'
    fields = ['name', 'type']
    breadcrumb = _l("New column")

    def form_valid(self, form):
        form.instance.project = Project.objects.get(name_short=self.kwargs['project'])
        return super(KanbanColumnCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('project:edit', kwargs={'project': self.kwargs['project']})

    def test_func(self):
        return get_w_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


class KanbanColumnUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = KanbanColumn
    template_name = 'kanbancol/update_kanbancolumn.html'
    breadcrumb = _("Settings")
    form_class = KanbanColumnForm

    def get_success_url(self):
        return reverse('project:edit', kwargs={'project': self.kwargs['project']})

    def test_func(self):
        return get_w_object_or_404(self.request.user, KanbanColumn,
                                   project__name_short=self.kwargs.get('project'),
                                   position=self.kwargs.get('position'))

    def get_object(self):
        return get_w_object_or_404(self.request.user, KanbanColumn,
                                   project__name_short=self.kwargs.get('project'),
                                   position=self.kwargs.get('position'))


class KanbanColumnUpView(LoginRequiredMixin, UserPassesTestMixin, View):

    def post(self, request, *args, **kwargs):
        kc = get_w_object_or_404(self.request.user, KanbanColumn,
                                 project__name_short=self.kwargs['project'],
                                 position=self.kwargs['position'])
        kc.switch(kc.position-1)
        return redirect(reverse('project:edit', kwargs={'project': self.kwargs['project']}))

    def test_func(self):
        return get_w_object_or_404(self.request.user, KanbanColumn,
                                   project__name_short=self.kwargs.get('project'),
                                   position=self.kwargs.get('position'))

    def get(self, *args, **kwargs):
        raise Http404


class KanbanColumnDownView(LoginRequiredMixin, UserPassesTestMixin, View):

    def post(self, request, *args, **kwargs):
        kc = get_w_object_or_404(self.request.user, KanbanColumn,
                                 project__name_short=self.kwargs['project'],
                                 position=self.kwargs['position'])
        kc.switch(kc.position+1)
        return redirect(reverse('project:edit', kwargs={'project': self.kwargs['project']}))

    def test_func(self):
        return get_w_object_or_404(self.request.user, KanbanColumn,
                                   project__name_short=self.kwargs.get('project'),
                                   position=self.kwargs.get('position'))

    def get(self, *args, **kwargs):
        raise Http404


class KanbanColumnDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = KanbanColumn
    template_name = 'confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        if 'delete' in request.POST:
            if self.get_object().issues.not_archived().count() != 0:
                messages.add_message(request, messages.ERROR,
                                     _('Kanban column has issues assigned, delete was rejected.'))
            elif (self.get_object().type == 'Done' and
                  self.get_object().project.kanbancol.filter(type='Done').count() == 1):
                messages.add_message(request, messages.ERROR,
                                     _('You can not delete the only column with type Done, delete was rejected.'))
            elif (self.get_object().type == 'ToDo' and
                  self.get_object().project.kanbancol.filter(type='ToDo').count() == 1):
                messages.add_message(request, messages.ERROR,
                                     _('You can not delete the only column with type Todo, delete was rejected.'))
            else:
                self.get_object().delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('project:edit', kwargs={'project': self.kwargs['project']})

    def test_func(self):
        return get_w_object_or_404(self.request.user, KanbanColumn,
                                   project__name_short=self.kwargs.get('project'),
                                   position=self.kwargs.get('position'))

    def get_object(self):
        return get_w_object_or_404(self.request.user, KanbanColumn,
                                   project__name_short=self.kwargs.get('project'),
                                   position=self.kwargs.get('position'))
