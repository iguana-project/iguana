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
from django import template
from django.urls import resolve
from django.http import Http404
from django.utils.translation import ugettext as _

from common.views import BreadcrumbView

register = template.Library()


class Breadcrumb():
    def __init__(self, label, url):
        self.label = label
        self.url = url

    def __eq__(self, other):
        return self.label == other.label and self.url == other.url

    def __str__(self):
        return self.label


@register.inclusion_tag("breadcrumbs.html", takes_context=True)
def breadcrumbs(context):
    url = context["request"].path
    breadcrumbs = []
    toplevel = True
    while True:
        try:
            func, args, kwargs = resolve(url)
        except Http404:
            pass
        else:
            if hasattr(func, "view_class"):
                view = func.view_class
                label = func.view_initkwargs.get("breadcrumb")
                if label:
                    pass
                elif hasattr(view, "get_breadcrumb"):
                    label = view().get_breadcrumb(*args, **kwargs)
                elif hasattr(view, "breadcrumb"):
                    label = view.breadcrumb
                else:
                    label = view.__name__
                # allow views to turn of breadcrumbs
                if toplevel and hasattr(view, "hide_breadcrumbs") and view.hide_breadcrumbs:
                    return {'show': False}
                toplevel = False
                # allow views to not add a crumb by returning an empty string
                if label:
                    if issubclass(view, BreadcrumbView):
                        breadcrumbs.append(Breadcrumb(label, ""))
                    else:
                        breadcrumbs.append(Breadcrumb(label, url))
        # remove one layer from the url and always have a slash in the front and
        # the back for consistency and because some urls need the slash in the
        # back
        url = "/" + "/".join([x for x in url.split("/") if x][:-1]) + "/"
        if url == "//":
            break
    breadcrumbs.reverse()
    return {'show': True, 'breadcrumbs': breadcrumbs}
