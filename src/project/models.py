"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from search.fieldcheckings import SearchableMixin
from django.urls import reverse

from common.settings import AUTH_USER_MODEL
from lib.custom_model import CustomModel

from django.utils.translation import ugettext_lazy as _
from cuser.middleware import CuserMiddleware
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache


import json


# no CustomModel required since object is used within models.py only
class ProjectQuerySet(models.QuerySet):
    def latest_projects(self, user):
        return self.all().order_by('updated_at')[:5]


# no CustomModel required since object is used within models.py only
class ProjectManager(models.Manager):
    class Meta:
        verbose_name = _("projectmanager")
        verbose_name_plural = _("projectmanagers")

    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)

    def latest_projects(self):
        return self.get_queryset().latest_projects()


class Project(SearchableMixin, CustomModel):
    name = models.CharField(
            _("Name"),
            max_length=30,
            validators=[
                MinLengthValidator(4, _("A Projectname should be at least 4 chars long"))
            ],
           )

    activity = models.TextField(default="[]")

    name_short = models.CharField(_("Short Name"),
                                  max_length=4,
                                  unique=True,
                                  validators=[
                                    RegexValidator(r'^[0-9a-zA-Z]*$', _("Only alphanumeric characters are valid"))
                                  ],
                                  )
    description = models.TextField(_("Description"), blank=True)
    creator = models.ForeignKey(AUTH_USER_MODEL,
                                # TODO BUG the project should not be deleted when the creator is deleted
                                on_delete=models.CASCADE,
                                verbose_name=_("creator"),
                                related_name="creator"
                                )
    created_at = models.DateTimeField(_("Creation Date"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last updated:"), auto_now=True)
    manager = models.ManyToManyField(AUTH_USER_MODEL,
                                     verbose_name=_("project manager"),
                                     related_name="manager"
                                     )
    developer = models.ManyToManyField(AUTH_USER_MODEL,
                                       verbose_name=_("developer"),
                                       related_name="dev_projects",
                                       blank=True
                                       )
    # TODO BUG projectWhereWctive? is that a typo what is meant with Wctive? (=active?)
    currentsprint = models.ForeignKey('sprint.Sprint',
                                      models.CASCADE,
                                      verbose_name=_("sprint"),
                                      related_name="projectWhereWctive",
                                      default=None,
                                      blank=True,
                                      null=True
                                      )

    nextTicketId = models.IntegerField(_("Next ticket ID"), editable=False, default=1)
    nextSprintId = models.IntegerField(_("Next sprint ID"), editable=False, default=1)

    activity_only_for_managers = models.BooleanField(_("Only managers can see timelog statistics for all developers"),
                                                     default=True)

    objects = ProjectManager()

    class Meta:
        ordering = ['name']
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def get_absolute_url(self):
        return reverse('project:detail', kwargs={'project': self.name_short})

    def has_active_sprint(self):
        if (self.currentsprint is not None):
            return (self.currentsprint.is_active())
        else:
            return False

    def developer_allowed(self, user):
        if (len(self.manager.filter(pk=user.pk)) == 1 or
           len(self.developer.filter(pk=user.pk)) == 1):
            return 1
        return 0

    def is_manager(self, user):
        if len(self.manager.filter(pk=user.pk)) == 1:
            return 1
        return 0

    def get_members(self):
        return (self.developer.all() | self.manager.all()).distinct()

    def __str__(self):
        return self.name

    # SearchableMixin functions
    def search_allowed_for_user(self, user):
        return self.developer_allowed(user)

    def get_relative_project(self):
        return self.name

    # permission functions
    def user_has_write_permissions(self, user):
        return self.is_manager(user)

    def user_has_read_permissions(self, user):
        return self.developer_allowed(user)

    # activity function
    def activity_stream_long_name(self):
        return self.description

    def increase_activity(self, date, issue=None, decrease=False):
        actor = CuserMiddleware.get_user()
        # handle user activity, if there is a current user
        if actor and not isinstance(actor, AnonymousUser):
            user_activity = json.loads(actor.activity)
            iss = 'None'
            if issue:
                iss = issue.get_ticket_identifier()
            if decrease:
                if self.name_short in user_activity:
                    user_activity[self.name_short].pop()
            else:
                if self.name_short in user_activity:
                    user_activity[self.name_short].append((date.isoformat(), iss))
                else:
                    user_activity[self.name_short] = []
                    user_activity[self.name_short].append((date.isoformat(), iss))
            actor.activity = json.dumps(user_activity)
            actor.save()
            # delete cache
            cache.delete('action_data_'+actor.username)
            cache.delete('action_data_'+actor.username+'_'+self.name_short)

        # handle project activity
        activity_dict = json.loads(self.activity)
        if isinstance(activity_dict, dict):
            activity_dict = []
        if decrease:
            activity_dict.pop()
        else:
            activity_dict.append(date.isoformat())
        self.activity = json.dumps(activity_dict)
        self.save()
        return

    searchable_fields = ['creator', 'created_at', 'description', 'name', 'name_short', 'updated_at', 'issue']
