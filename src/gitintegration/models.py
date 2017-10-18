"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from django.db.models.signals import post_save
from lib.custom_model import CustomModel
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from django.core.exceptions import ValidationError

import os
import stat
import json

from common.settings.common import REPOSITORY_ROOT, BASE_DIR

from project.models import Project
from issue.models import Issue
from search.fieldcheckings import SearchableMixin

from django.utils.translation import ugettext_lazy as _
# TODO BUG the open files need to be closed somehow


# provide upload target path for rsa keys
def get_upload_path(instance, filename):
    return "git_sshkeys/repo_" + instance.project.name_short + "/" + filename


def validate_local_path(value):
    # network protocols are always ok
    valid_protocols = ['git://', 'http://', 'https://', 'ftp://', 'ftps://']
    for p in valid_protocols:
        if value.startswith(p):
            return

    # local paths are forbidden
    raise ValidationError(_('Invalid repository path'),
                          params={'value': value},
                          )


class Repository(CustomModel):
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                verbose_name=_("project"),
                                related_name=_("repos"),
                                )
    url = models.CharField(_("Repository URL"),
                           max_length=256,
                           blank=False,
                           validators=[validate_local_path]
                           )
    rsa_priv_path = models.FileField(_("RSA private key"),
                                     upload_to=get_upload_path,
                                     max_length=128,
                                     )
    rsa_pub_path = models.FileField(_("RSA public key"),
                                    upload_to=get_upload_path,
                                    max_length=128,
                                    )
    conn_ok = models.BooleanField(_("Connection ok"),
                                  default=False,
                                  )
    last_commit_processed = models.CharField(_("Last commit processed"),
                                             max_length=40,
                                             default=''
                                             )

    def __str__(self):
        return "Repository " + self.url

    def get_local_repo_path(self):
        return os.path.join(REPOSITORY_ROOT, "repository_" + self.project.name_short + "_" + str(self.pk))

    def user_has_write_permissions(self, user):
        return self.project.is_manager(user)

    def user_has_read_permissions(self, user):
        return self.project.user_has_read_permissions(user)


@receiver(post_save, sender=Repository)
def set_file_permissions(sender, instance, *args, **kwargs):
    os.chmod(instance.rsa_priv_path.path, stat.S_IRUSR | stat.S_IWUSR)
    os.chmod(instance.rsa_pub_path.path, stat.S_IRUSR | stat.S_IWUSR)


class Commit(SearchableMixin, CustomModel):
    repository = models.ForeignKey('Repository',
                                   on_delete=models.CASCADE,
                                   verbose_name=_("Repository"),
                                   related_name=_("commits"),
                                   )
    issue = models.ForeignKey(Issue,
                              on_delete=models.CASCADE,
                              verbose_name=_("Issue"),
                              related_name=_("commits"),
                              )
    date = models.DateTimeField(_("Creation Date"))
    author = models.CharField(_("Author"),
                              max_length=128,
                              )
    name = models.CharField(_("Commit name"),
                            max_length=40,
                            )
    message = models.TextField(_("Commit message"),
                               blank=False,
                               )
    changes = models.TextField(_("Changes"),
                               blank=True,
                               )
    tags = models.TextField(_("Tags"),
                            blank=True,
                            )

    class Meta:
        # make repo and sha unique to prevent duplicates per repo
        unique_together = ('repository', 'name')
        ordering = ['-date']

    def __str__(self):
        return "Commit " + self.name

    def get_title(self):
        return self.message.split('\n', 1)[0]

    def get_name_short(self):
        return self.name[:7]

    def set_changes(self, changes):
        self.changes = json.dumps(changes)

    def get_changes(self):
        if self.changes != '':
            return json.loads(self.changes)
        return {}

    def set_tags(self, tags):
        self.tags = json.dumps(tags)

    def get_tags(self):
        if self.tags != '':
            return json.loads(self.tags)
        return {}

    def user_has_write_permissions(self, user):
        return self.repository.project.is_manager(user)

    def user_has_read_permissions(self, user):
        return self.repository.project.user_has_read_permissions(user)

    def search_allowed_for_user(self, user):
        return self.user_has_read_permissions(user)

    def get_search_title(self):
        return "(" + self.get_name_short() + ") " + self.get_title()

    def get_absolute_url(self):
        return reverse('issue:detail', kwargs={'project': self.issue.project.name_short, 'sqn_i': self.issue.number})

    searchable_fields = ['issue', 'date', 'author', 'name', 'message', 'changes']


@receiver(post_save, sender=Commit)
def set_project_activity_counter(sender, instance, *args, **kwargs):
    return instance.repository.project.increase_activity(timezone.now(), instance)
