"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic.base import TemplateView
from django.core.cache import cache

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l
from actstream.models import user_stream
from lib.show_more_mixin import ShowMoreMixin
from lib.activity_permissions import check_activity_permissions
from landing_page.actstream_util import unfollow_project
from project.models import Project


class HomeView(ShowMoreMixin, TemplateView):
    """
    The landing page.
    It shows a default home page if the user is not logged in.
    If he's logged in, it shows the user dashboard.
    """
    hide_breadcrumbs = True
    items_per_page = 15

    def get(self, request, *args, **kwargs):
        # show dashboard if a user is logged in
        if request.user.is_authenticated:
            self.template_name = "landing_page/dashboard.html"

            # check if the user wants to unfollow a project
            if request.GET.get("unfollow", "") != "":
                unfollow_project(request.user, Project.objects.get(pk=request.GET['unfollow']))

            # get the items of the activity stream
            self.item_list = cache.get('activity_items_'+request.user.username)
            if not self.item_list:
                self.item_list = check_activity_permissions(request.user, user_stream(request.user))
                cache.set('activity_items_'+request.user.username, self.item_list, 60*60*24*31)

        else:
            self.template_name = "landing_page/home.html"

        return TemplateView.get(self, request, *args, **kwargs)
