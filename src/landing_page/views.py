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


# no LoginRequiredMixin since another template (Welcome/home) is rendered for the same url when not logged in
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
