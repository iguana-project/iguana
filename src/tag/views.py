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
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.template.defaulttags import register
from django.urls import reverse
from django.shortcuts import render

from lib.custom_model import get_r_object_or_404
from .forms import TagForm
from .models import Tag
from project.models import Project
import json
from django.db import IntegrityError

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


# NOTE: we don't use CreateView, UpdateView, DeleteView here, because there might be no way to combine them in one form
# TODO BUG is there still the problem that we have internal server errors if internal database queries fail?
class TagView(LoginRequiredMixin, UserPassesTestMixin, View):
    form_class = TagForm
    breadcrumb = _l("")

    def post(self, request, *args, **kwargs):
        project = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        form = self.form_class(request.POST, project=project)

        if 'delete_tags' in request.POST:
            for tag in request.POST.getlist('delete_tags'):
                Tag.objects.filter(tag_text=tag, project=project).delete()
            return HttpResponseRedirect(reverse('tag:tag', kwargs={'project': self.kwargs.get('project')}),
                                        {'form': self.form_class(project=project)})

        if form.is_valid():
            if 'create_tag' in request.POST:
                if len(request.POST['color']) > 0 and request.POST['color'] != "i dont care":
                    new_tag = Tag(tag_text=request.POST['tag_text'], color=request.POST['color'], project=project)
                else:
                    new_tag = Tag(tag_text=request.POST['tag_text'], project=project)
                new_tag.save()

            return HttpResponseRedirect(reverse('tag:tag', kwargs={'project': self.kwargs.get('project')}),
                                        {'form': form})
        if request.is_ajax():
            return HttpResponse(form.errors.as_json(), status=500, content_type='application/json')

        tags = Tag.objects.filter(project=project)
        return render(request, 'tag/tag_manage.html', {'form': form,
                                                       'project': project, 'tags': tags})

    def get(self, request, *args, **kwargs):
        project = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        tags = Tag.objects.filter(project=project)
        return render(request, 'tag/tag_manage.html', {'form': self.form_class(project=project),
                                                       'project': project, 'tags': tags})

    # only developer and manager are allowed to change tag-settings
    def test_func(self):
        return get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))


@register.filter
def is_bright_color(color):
    return color in Tag.BRIGHT_COLORS
