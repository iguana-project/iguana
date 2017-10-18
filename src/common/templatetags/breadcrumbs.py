"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
