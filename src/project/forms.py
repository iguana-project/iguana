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
from django.forms import ModelForm, CharField

from .models import Project
from landing_page.actstream_util import unfollow_project

import json
from common.widgets import CustomPagedownWidget, CustomAutoCompleteWidgetMultiple


def remove_notification_settings(user, project):
    try:
        props = json.loads(user.get_preference('notify_mail'))

        if project.name_short in props:
            # project in settings, delete it and store
            del props[project.name_short]
            user.set_preference('notify_mail', json.dumps(props))
    except (TypeError, json.JSONDecodeError):
        # no props => nothing to delete => return
        return


def clear_assignee_follow_m2m_fields_for_users(users, project):
        for user in users:
            issues = user.issues.filter(project=project)
            for iss in issues:
                iss.assignee.remove(user)
            issues = user.discussing.filter(project=project)
            for iss in issues:
                iss.participant.remove(user)
            for noti in user.notifications.filter(issue__project=project):
                noti.delete()
            unfollow_project(user, project)
            remove_notification_settings(user, project)


class ProjectCreateForm(ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'name_short', 'description', 'developer')
        widgets = {
            'developer': CustomAutoCompleteWidgetMultiple('project:userac',
                                                          attrs={'data-html': 'true',
                                                                 'data-minimum-input-length': 2
                                                                 }
                                                          )
        }


class ProjectEditForm(ModelForm):
    description = CharField(widget=CustomPagedownWidget(),
                            required=False)

    class Meta:
        model = Project
        fields = ('name', 'description', 'manager', 'developer', 'activity_only_for_managers')
        widgets = {
            'developer': CustomAutoCompleteWidgetMultiple('project:userac', attrs={'data-html': 'true'}),
            'manager': CustomAutoCompleteWidgetMultiple('project:userac', attrs={'data-html': 'true'})
        }

    def save(self, commit=True):
        before = list(self.instance.get_members())
        self.instance = super(ProjectEditForm, self).save()
        after = list(self.instance.get_members())
        diff = []
        for user in before:
            if user not in after:
                diff.append(user)
        clear_assignee_follow_m2m_fields_for_users(diff, self.instance)
        return self.instance
