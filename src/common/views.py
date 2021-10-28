"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
