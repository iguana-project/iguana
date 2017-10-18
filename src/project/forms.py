"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import ModelForm, CharField
from dal import autocomplete
from pagedown.widgets import PagedownWidget

from .models import Project
from landing_page.actstream_util import unfollow_project

import json


def remove_notification_settings(user, project):
    try:
        props = json.loads(user.get_preference('notify_mail'))

        if project.name_short in props:
            # project in settings, delete it and store
            del props[project.name_short]
            user.set_preference('notify_mail', json.dumps(props))
    except:
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
                'developer': autocomplete.ModelSelect2Multiple('project:userac',
                                                               attrs={'data-html': 'true',
                                                                      'data-minimum-input-length': 2
                                                                      }
                                                               )
        }


class ProjectEditForm(ModelForm):
    description = CharField(widget=PagedownWidget(css=("pagedown/demo/browser/demo.css", "css/pagedown.css")),
                            required=False)

    class Meta:
        model = Project
        fields = ('name', 'description', 'manager', 'developer', 'activity_only_for_managers')
        widgets = {
                'developer': autocomplete.ModelSelect2Multiple('project:userac', attrs={'data-html': 'true'}),
                'manager': autocomplete.ModelSelect2Multiple('project:userac', attrs={'data-html': 'true'})
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
