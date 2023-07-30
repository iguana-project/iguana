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
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.db import transaction
from django.urls.base import reverse
from django.utils import translation
from django.utils.datastructures import MultiValueDictKeyError
from django.shortcuts import redirect
from django.core.cache import cache
from django.http import Http404
from lib.multiform import MultiFormsView, MultiFormMixin

from actstream.models import actor_stream
from issue.models import Issue
from lib.custom_model import get_r_object_or_404, get_w_object_or_404
from lib.show_more_mixin import ShowMoreMixin
from project.models import Project
from user_profile.forms import CustomUserChangeForm, CustomPasswordChangeForm
from discussion.models import Notitype

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l
from lib.activity_permissions import check_activity_permissions

import json


class ToggleNotificationView(LoginRequiredMixin, UserPassesTestMixin, View):
    # receiving:
    #   shn_p
    #   notiway (e.g. mail)
    #   notitype (e.g. NewIssue)
    #   enabled (1/0)
    rcvs = ['shn_p', 'notiway', 'notitype', 'enabled']

    def post(self, request, *args, **kwargs):
        # check whether the user is in given project is already performed in test_func()
        rcvs = self.rcvs
        # check presence
        if not set(rcvs).issubset(list(self.request.POST.keys())):
            raise Http404()

        # check that notitype is valid
        valid_notitypes = []
        for t in Notitype.NOTI_TYPES:
            valid_notitypes.append(t[0])

        if self.request.POST.get(rcvs[2]) not in valid_notitypes:
            raise Http404()

        propname = "notify_" + self.request.POST.get(rcvs[1])

        props = {}
        try:
            props = json.loads(self.request.user.get_preference(propname))
        except (TypeError, json.JSONDecodeError):
            # currently no settings for property, this is okay
            pass

        # load project's properties
        props_proj = props.get(self.request.POST.get(rcvs[0]), [])

        if self.request.POST.get(rcvs[3]) == '1':
            # shall be enabled
            if self.request.POST.get(rcvs[2]) not in props_proj:
                props_proj.append(self.request.POST.get(rcvs[2]))

        if self.request.POST.get(rcvs[3]) == '0':
            # shall be disabled
            if self.request.POST.get(rcvs[2]) in props_proj:
                props_proj.remove(self.request.POST.get(rcvs[2]))

        props[self.request.POST.get(rcvs[0])] = props_proj
        self.request.user.set_preference(propname, json.dumps(props))

        self.request.session['nocollapse'] = self.request.POST.get(rcvs[0])

        return redirect(reverse('user_profile:user_profile_page', kwargs={'username': self.request.user.username}))

    def test_func(self):
        # user needs read permissions for the project
        rcvs = self.rcvs
        return get_r_object_or_404(self.request.user, Project, name_short=self.request.POST.get(rcvs[0]))


class ShowProfilePageView(LoginRequiredMixin, ShowMoreMixin, DetailView):
    model = get_user_model()
    template_name = 'user_profile/user_profile_page.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'user'
    items_per_page = 20

    def get_context_data(self, **kwargs):
        # get the user for this profile page
        user = get_r_object_or_404(self.request.user, get_user_model(), username=self.kwargs.get("username"))
        # get the actor stream for the requested user profile
        item_list = cache.get('activity_items_actor_'+user.username)
        if not item_list:
            item_list = actor_stream(user)
            cache.set('activity_items_actor_'+user.username, item_list, 60*60*24*31)

        # filter out actions with targets the requesting user is not part of
        self.item_list = check_activity_permissions(self.request.user, item_list)

        # get this user
        selfuser = get_r_object_or_404(self.request.user, get_user_model(), username=self.request.user.username)
        sharedprojects = Project.objects.filter(developer=user).filter(developer=selfuser)
        sharedissues = Issue.objects.filter(assignee=user).filter(assignee=selfuser)

        # create the context
        context = super(ShowProfilePageView, self).get_context_data(**kwargs)
        context['sharedprojects'] = sharedprojects
        context['sharedissues'] = sharedissues
        context['nocollapse'] = self.request.session.get('nocollapse', '')
        if context['nocollapse'] != '':
            del self.request.session['nocollapse']

        # add data for notifications

        prefs = {}
        try:
            prefs = json.loads(user.get_preference('notify_mail'))
        except (TypeError, json.JSONDecodeError):
            pass

        # there shall be an entry for every project the user is member of
        for uproj in user.get_projects():
            if uproj.name_short not in prefs:
                prefs[uproj.name_short] = []

        context['notify_mail'] = prefs

        notitypes = []

        for t in Notitype.NOTI_TYPES:
            notitypes.append([t[0], t[1]])

        context['possible_notis'] = notitypes

        # add data for activity chart type
        if self.request.GET.get('data') is not None:
            self.request.user.set_preference('activity_chart_type',
                                             self.request.GET.get('data'))
        data = self.request.user.get_preference('activity_chart_type',
                                                default="timelog")
        context['chart_type'] = data

        return context

    def get_breadcrumb(self, *args, **kwargs):
        return kwargs['username']


class EditProfilePageView(LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, MultiFormsView):
    model = get_user_model()
    template_name = 'user_profile/edit_user_profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'user'
    form_classes = {
        'userChange': CustomUserChangeForm,
        'passwordChange': CustomPasswordChangeForm
    }
    avatar_kwargs = {}
    breadcrumb = _l("Edit")

    def get_success_url(self, form_name=None):
        return reverse('user_profile:user_profile_page', kwargs={"username": self.kwargs.get("username")})

    def create_passwordChange_form(self, **kwargs):
        return CustomPasswordChangeForm(kwargs.pop('instance'), **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(EditProfilePageView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # set language key
        request.session[translation.LANGUAGE_SESSION_KEY] = request.POST['language']

        # if a new avatar image was set, save it as the 'old' one
        self.avatar_kwargs = {'old_avatar_name': self.object.avatar.name}

        # Changing the email address should not be possible without entering the correct password!!
        # Normally this is a check one want in the clean-methods of those forms, but there it is not possible to access
        # elements of other forms, so this is a dirty workaround.
        # TODO maybe it is possible to provide this error to the respective clean-functions
        username = self.kwargs.get('username')
        # this should make this situation TOCTOU-safe
        # in case it doesn't try to use select_for_update()
        with transaction.atomic():
            # NOTE: this has to be part of the atomic block!
            current_user = get_user_model().objects.get(username=username)
            old_email = current_user.email
            forms = request.POST
            new_email = forms['email']
            wrong_password = False

            if old_email != new_email:
                try:
                    provided_password = forms['old_password']
                except (TypeError, MultiValueDictKeyError):
                    provided_password = None

                if(provided_password is None or provided_password == "" or
                   authenticate(username=username, password=provided_password) is None):
                    wrong_password = True

        # NOTE: in this case we shall not call save (super)
        if wrong_password:
            messages.add_message(request, messages.ERROR,
                                 _('You can not change the email address without entering the correct password.' +
                                   'All changes have been discarded!'))
            # TODO copy elements? - this might be some pain because we have to split those elements on both forms
            return super(EditProfilePageView, self).get(request, *args, **kwargs)

        response = super(EditProfilePageView, self).post(request, *args, **kwargs)

        current_user = get_user_model().objects.get(username=username)

        if response.status_code == 200:
            messages.add_message(request, messages.ERROR,
                                 _('Something went wrong, one or more field credentials are not fulfilled'))
        else:
            messages.add_message(request, messages.SUCCESS, _('Profile successfully edited.'))
        return response

    def passwordChange_form_valid(self, forms, form):
        self.object = form.save()
        # login with the new password
        login(self.request, self.object)
        return super(EditProfilePageView, self).form_valid(forms, form)

    def userChange_form_valid(self, forms, form):
        self.object = form.save(**self.avatar_kwargs)
        return super(EditProfilePageView, self).form_valid(forms, form)

    def test_func(self):
        # the user can only edit it's own profile
        return get_w_object_or_404(self.request.user, get_user_model(), username=self.kwargs.get("username"))
