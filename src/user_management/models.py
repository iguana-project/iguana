"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import pytz
import os

from django.db import models
from django.db.models import TextField
from django.contrib.auth.models import AbstractUser
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _

from lib.custom_model import CustomModel

from issue.models import Issue
from project.models import Project
from search.fieldcheckings import SearchableMixin

# https://docs.djangoproject.com/en/1.10/topics/auth/customizing/#auth-custom-user


def avatarDir(instance, filename):
    """
    This method returns the avatar directory for the current logged in user
    """
    return 'avatars/{}/{}'.format(instance.username, filename)


class CustomUser(SearchableMixin, AbstractUser, CustomModel):
    # NOTE: if we need some additional fields we might add those fields into the settings/common.py
    # NOTE: into the UserAttributeSimilarityValidator
    # NOTE: plus if one field name is changed, we also need to adjust ^this
    class Meta:
        # the verbose values are required to identify the user model as "user" and not "customuser"
        verbose_name = getattr(AbstractUser, "_meta").verbose_name
        verbose_name_plural = getattr(AbstractUser, "_meta").verbose_name_plural

        # avoid 'UnorderedObjectListWarning'
        ordering = ["username"]

    email = models.EmailField(_('email address'), unique=True)

    # additional fields (first and last name are already part of AbstractUser)
    avatar = models.ImageField(_('avatar'), upload_to=avatarDir, default=os.path.join("avatars", "default.svg"))
    LANGUAGES = (
        ('en', _("English")),
        ('de', _("German")),
    )
    language = models.CharField(_('language'), max_length=2, choices=LANGUAGES, default='en')
    timezone = models.CharField(_('timezone'), max_length=255, default='UTC',
                                choices=[(x, x) for x in pytz.common_timezones])

    show_activity_to_other_users = models.BooleanField(_("""Others can see your activity
                                                         heatmap on your profile page"""),
                                                       default=True)
    # TODO: any other fields wanted?

    activity = TextField(default='{}')

    def get_projects(self):
        return (self.manager.all() | self.dev_projects.all()).distinct()

    def get_absolute_url(self):
        return reverse('user_profile:user_profile_page', kwargs={"username": self.username})

    def __str__(self):
        username = self.first_name
        if self.first_name and self.last_name:
            username += ' '
        username += self.last_name
        if not username:
            username = self.username
        return username

    def get_preference(self, key, default=None):
        result = self.preferences.filter(key=key)
        if len(result) == 1:
            return result.first().value
        return default

    def set_preference(self, key, value):
        result = self.preferences.filter(key=key)
        if len(result) == 1:
            # key already present => update value
            pref = result.first()
            if value is None:
                # delete key if value is None
                pref.delete()
            else:
                pref.value = value
                pref.save()
        else:
            # key not present => create new preference object
            pref = UserPreference(user=self, key=key, value=value)
            pref.save()
            self.preferences.add(pref)

    @classmethod
    def get_search_name(cls):
        return "User"

    searchable_fields = ['first_name', 'last_name', 'username']

    # every user profile is public
    def user_has_read_permissions(self, user):
        return True

    def user_has_write_permissions(self, user):
        return self == user


class UserPreference(CustomModel):
    user = models.ForeignKey('CustomUser',
                             models.CASCADE,
                             verbose_name=_("user"),
                             related_name="preferences",
                             )
    key = models.CharField(_('key'),
                           max_length=100,
                           )
    value = models.TextField(_('value'),
                             )

    class Meta:
        unique_together = (("user", "key"),)

    def __str__(self):
        return self.key + ": " + self.value

    def user_has_read_permissions(self, user):
        return self.user == user

    def user_has_write_permissions(self, user):
        return self.user == user
