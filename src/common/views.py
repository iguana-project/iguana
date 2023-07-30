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
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.static import serve

from common import settings

from .models import Filter
from dal.autocomplete import Select2QuerySetView


USE_X_ACCEL_REDIRECT = getattr(settings, 'USE_X_ACCEL_REDIRECT', False)
X_ACCEL_REDIRECT_PREFIX = getattr(settings, 'X_ACCEL_REDIRECT_PREFIX', None)


# Even though this view is shown only within another view that already should implement the LoginRequiredMixin,
# it is added here to prevent information leakage due to possible bugs in other places.
class BreadcrumbView(LoginRequiredMixin, View):
    """
    This View can be used to insert a breadcrumblayer without putting content at
    that layer.

        url(r'^foo/?', BreadcrumbView.as_view(breadcrumb="foo")),
        url(r'^foo/bar?', SomeView.as_view()),
    """
    breadcrumb = ""

    def get(self, *args, **kwargs):
        raise Http404


class ShowProtectedFilesView(LoginRequiredMixin, View):
    """
    This View is basically an internal redirect to deliver files. Since the media directory is 'internal' in the
    nginx settings, neither the media directory or any of it's content is not accessible via a URL,
    but only from within Django. Therefore it passes some permission checks first.
    """
    def get(self, request, content_disposition_type="inline", *args, **kwargs):
        if USE_X_ACCEL_REDIRECT:
            response = HttpResponse('')
            if X_ACCEL_REDIRECT_PREFIX is not None:
                first_path_element = re.compile("^/([^/]*)/").search(request.path).group(1)
                request.path = request.path.replace(first_path_element, X_ACCEL_REDIRECT_PREFIX, 1)
            response['X-Accel-Redirect'] = request.path
            response['Content-Type'] = ''

        else:
            response = serve(request, request.path, settings.FILES_DIR)

        return response


class CreateFilterView(LoginRequiredMixin, View):
    def get_success_url(self):
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse('issue:issue_list_all_view')

    def post(self, request, *args, **kwargs):
        user = self.request.user
        filter_string = self.request.POST.get('string')
        delete = self.request.POST.get('delete', 'false')
        if delete == 'true':
            # even if the queryset is empty there are no problems
            Filter.objects.filter(user=user, queryset=filter_string).delete()
            return HttpResponseRedirect(self.get_success_url())

        if filter_string:
            name = self.request.POST.get('name')
            if not re.match(r"^[\w\s,.]+$", name) or len(name) > 99:
                messages.add_message(request,
                                     messages.WARNING,
                                     _("""Filter name can only contain letters, numbers, commas or periods.
                                       Maximum length is 99 characters""")
                                     )
                return HttpResponseRedirect(self.get_success_url()[:-10])

            typ = self.request.POST.get('typ')
            check = Filter.objects.filter(user=user, typ=typ, queryset=filter_string)
            if check.exists():
                messages.add_message(request,
                                     messages.WARNING,
                                     _("You already have a saved filter for that querystring") +
                                     ": " + check.first().name)
                return HttpResponseRedirect(self.get_success_url())
            if Filter.objects.filter(user=user, name=name, typ=typ).exists():
                messages.add_message(request, messages.WARNING,
                                     _("You already have a saved filter with the name") + ": " + name)
                return HttpResponseRedirect(self.get_success_url())

            Filter(user=user, queryset=filter_string, typ=typ, name=name).save()
        return HttpResponseRedirect(self.get_success_url())


# Even though this view should only show information dependent on the user logged in and hence the LoginRequiredMixin
# is not mandatory, it is added here to prevent information leakage due to possible bugs in other places.
class AutoCompleteView(LoginRequiredMixin, Select2QuerySetView):
    def get_results(self, context):
        return [
            {
                'id': self.get_result_value(result),
                'text': self.get_result_label_html(result),
                'cleaned_text': self.get_result_label_clean(result),
                'selected_text': self.get_result_label_html(result),
            } for result in context['object_list']
        ]

    def get_result_label_html(self, result):
        return self.get_result_label(result)

    def get_result_label_clean(self, result):
        return self.get_result_label(result)
