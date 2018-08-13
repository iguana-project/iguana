"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.core.validators import MinValueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from os.path import basename

from common.validators import date_is_present_or_future
import datetime
import json
from kanbancol.models import KanbanColumn
from project.models import Project
from sprint.models import Sprint
from tag.models import Tag
from common import *
from landing_page.actstream_util import unfollow_issue, follow_issue
from actstream.models import followers

from search.fieldcheckings import SearchableMixin

from django.utils.translation import ugettext_lazy as _
from lib.custom_model import CustomModel


@transaction.atomic
def get_number_for_ticket(project):
    retval = project.nextTicketId
    project.nextTicketId += 1
    project.save()
    return retval


@transaction.atomic
def get_number_for_comment(issue):
    retval = issue.nextCommentId
    issue.nextCommentId += 1
    issue.save()
    return retval


@transaction.atomic
def get_number_for_attachment(issue):
    retval = issue.nextAttachmentId
    issue.nextAttachmentId += 1
    issue.save()
    return retval


@transaction.atomic
def get_number_for_timelog(issue):
    retval = issue.nextTimelogId
    issue.nextTimelogId += 1
    issue.save()
    return retval


def get_upload_path(instance, filename):
    return "attachments/" + str(instance.issue.pk) + "/" + instance.file.name


class Attachment(SearchableMixin, CustomModel):
    seqnum = models.IntegerField(_("Attachment number"), editable=False, default=-1)
    file = models.FileField(_("File"),
                            upload_to=get_upload_path,
                            max_length=256,
                            )
    when = models.DateTimeField(_("Uploaded at"),
                                validators=[
                                    date_is_present_or_future
                                ],
                                editable=False,
                                blank=False,
                                default=timezone.now,
                                )
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                models.CASCADE,
                                verbose_name=_("creator"),
                                blank=False,
                                editable=False,
                                )
    issue = models.ForeignKey('Issue',
                              models.CASCADE,
                              verbose_name=_("issue"),
                              related_name="attachments",
                              editable=False,
                              )

    class Meta:
        ordering = ['when']
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    def get_absolute_url(self):
        return reverse('issue:detail', kwargs={'project': self.issue.project.name_short, 'sqn_i': self.issue.number})

    def __str__(self):
        return basename(self.file.name)

    def search_allowed_for_user(self, user):
        return self.issue.project.developer_allowed(user)

    def user_has_write_permissions(self, user):
        return self.creator == user

    def user_has_read_permissions(self, user):
        return self.issue.user_has_read_permissions(user)

    searchable_fields = ['when', 'creator', 'issue']


@receiver(pre_save, sender=Attachment)
def set_attachment_number(sender, instance, *args, **kwargs):
    if instance.seqnum == -1:
        instance.seqnum = get_number_for_attachment(instance.issue)
    return


class Comment(SearchableMixin, CustomModel):
    seqnum = models.IntegerField(_("Comment number"), editable=False, default=-1)
    when = models.DateTimeField(_("Created at"),
                                validators=[
                                    date_is_present_or_future
                                ],
                                editable=False,
                                blank=False,
                                default=timezone.now,
                                )
    modified = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                models.CASCADE,
                                verbose_name=_("creator"),
                                blank=False,
                                editable=False,
                                )
    issue = models.ForeignKey('Issue',
                              models.CASCADE,
                              verbose_name=_("issue"),
                              related_name="comments",
                              editable=False,
                              )
    text = models.TextField(_("Comment"),
                            blank=False,
                            )

    attachment = models.ForeignKey('Attachment',
                                   models.SET_NULL,
                                   verbose_name=_("attachment"),
                                   null=True,
                                   editable=False
                                   )

    class Meta:
        ordering = ['when']
        verbose_name = _("comment")
        verbose_name_plural = _("comments")

    def save(self, *args, **kwargs):
        if self.id and Comment.objects.get(id=self.id).text != self.text:
            self.modified = timezone.now()
        return super(Comment, self).save(*args, **kwargs)

    def get_absolute_url(self):
        url = reverse('issue:detail', kwargs={'project': self.issue.project.name_short, 'sqn_i': self.issue.number})
        url += '#comment'+str(self.seqnum)
        return url

    def __str__(self):
        return self.issue.__str__() + ":Comment" + str(self.seqnum)

    # SearchableMixin functions
    def search_allowed_for_user(self, user):
        return self.issue.project.developer_allowed(user)

    def get_relative_project(self):
        return self.issue.project.name

    # permission functions
    def user_has_write_permissions(self, user):
        return self.creator == user

    def user_has_read_permissions(self, user):
        return self.issue.user_has_read_permissions(user)

    # activity functions
    def activity_stream_short_name(self):
        return "Comment"

    def activity_stream_long_name(self):
        return self.text

    searchable_fields = ['when', 'creator', 'issue', 'text']


@receiver(pre_save, sender=Comment)
def set_comment_number(sender, instance, *args, **kwargs):
    if instance.seqnum == -1:
        instance.seqnum = get_number_for_comment(instance.issue)
    else:
        # comment edit, new comment handled in get_number_for_comment via issue.save()
        old = Comment.objects.get(issue=instance.issue, seqnum=instance.seqnum)
        if old.text != instance.text:
            instance.issue.project.increase_activity(timezone.now(), instance.issue)
    return


class IssueQuerySet(models.QuerySet):
    def without_sprint(self):
        return self.filter(sprint__isnull=True)

    def current_sprint(self):
        return self.filter(sprint__startdate__isnull=False, sprint__enddate__isnull=True)

    def archived(self):
        return self.filter(archived=True)

    def not_archived(self):
        return self.filter(archived=False)

    def not_done(self):
        return self.exclude(kanbancol__type='Done')


class Issue(SearchableMixin, CustomModel):
    title = models.CharField(_("Title"), max_length=100)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    project = models.ForeignKey(Project, models.CASCADE, verbose_name=_("project"), related_name="issue")
    sprint = models.ForeignKey(Sprint,
                               models.CASCADE,
                               verbose_name=_("sprint"),
                               related_name="issue",
                               default=None,
                               blank=True,
                               null=True
                               )
    number = models.IntegerField(_("Ticket number"), editable=False, default=-1)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                models.CASCADE,
                                verbose_name=_("creator"),
                                null=True,
                                editable=False,
                                )
    participant = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         verbose_name=_("participant"),
                                         related_name="discussing",
                                         editable=False,
                                         )
    kanbancol = models.ForeignKey(KanbanColumn, models.CASCADE, verbose_name=_("status"), related_name="issues")
    TICKET_TYPES = (
        ('Bug', _("Bug")),
        ('Story', _("Story")),
        ('Task', _("Task")),
    )
    type = models.CharField(
        _("Type"),
        max_length=5,
        choices=TICKET_TYPES,
        default='Task',
    )
    assignee = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      verbose_name=_("assignee"),
                                      related_name="issues",
                                      blank=True,
                                      )
    due_date = models.DateField(
        _("Due Date"),
        validators=[
            date_is_present_or_future
        ],
        blank=True,
        null=True,
    )
    PRIORITY_TYPES = (
        (0, _("Unimportant")),
        (1, _("Low")),
        (2, _("Medium")),
        (3, _("High")),
        (4, _("Critical")),
    )
    priority = models.IntegerField(
        _("Priority"),
        choices=PRIORITY_TYPES,
        default=2,
    )
    description = models.TextField(
        _("Description"),
        blank=True,
    )
    storypoints = models.IntegerField(
        _("Story Points"),
        # TODO it would be cool if the relative field in the template would not allow values less than 1
        validators=[
            MinValueValidator(0, _("Enter a positive storypoints amount!"))
        ],
        default=0
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="issues")
    dependsOn = models.ManyToManyField('Issue',
                                       verbose_name=_("depends on"),
                                       related_name="dependent",
                                       blank=True,
                                       )
    objects = IssueQuerySet.as_manager()
    nextCommentId = models.IntegerField(_("Next comment ID"), editable=False, default=1)
    nextAttachmentId = models.IntegerField(_("Next attachment ID"), editable=False, default=1)
    nextTimelogId = models.IntegerField(_("Next Timelog ID"), editable=False, default=1)
    was_in_sprint = models.BooleanField(_("was in a sprint"), editable=False, default=False)
    archived = models.BooleanField(_("archived"), editable=False, default=False)
    logged_total = models.DurationField(_("Logged time"), default=datetime.timedelta(seconds=0))

    searchable_fields = ['project', 'sprint', 'description', 'kanbancol', 'assignee', 'due_date', 'tags',
                         'number', 'priority', 'storypoints', 'title', 'type', 'creator']

    class Meta:
        ordering = ['number']
        base_manager_name = 'objects'
        verbose_name = _("issue")
        verbose_name_plural = _("issues")

    def __str__(self):
        return self.title

    def get_ticket_identifier(self):
        return self.project.name_short + "-" + str(self.number)

    def get_left_kCol_for_issue(self):
        left_columns = self.project.kanbancol.filter(position__lt=self.kanbancol.position)
        if left_columns.count() == 0:
            return -1
        return left_columns.last().position

    def get_right_kCol_for_issue(self):
        right_columns = self.project.kanbancol.filter(position__gt=self.kanbancol.position)
        if right_columns.count() == 0:
            return -1
        return right_columns.first().position

    def get_absolute_url(self):
        return reverse('issue:detail', kwargs={'project': self.project.name_short, 'sqn_i': self.number})

    # SearchableMixin functions
    def search_allowed_for_user(self, user):
        return self.project.developer_allowed(user)

    def get_search_title(self):
        return "(" + self.get_ticket_identifier() + ") " + self.title

    def get_relative_project(self):
        return self.project.name

    # permission functions
    def user_has_write_permissions(self, user):
        return self.project.user_has_write_permissions(user)

    def user_has_read_permissions(self, user):
        return self.project.user_has_read_permissions(user)

    # activity functions
    def activity_stream_short_name(self):
        return self.get_ticket_identifier()

    def activity_stream_long_name(self):
        return self.__str__()


@receiver(pre_save, sender=Issue)
def set_ticket_number(sender, instance, *args, **kwargs):
    if instance.number == -1:
        instance.number = get_number_for_ticket(instance.project)
    return


@receiver(post_save, sender=Issue)
def set_project_activity_counter(sender, instance, *args, **kwargs):
    return instance.project.increase_activity(timezone.now(), instance)


@receiver(pre_save, sender=Issue)
def handle_follow_unfollow_on_archive_unarchive(sender, instance, *args, **kwargs):
    try:
        old = Issue.objects.get(project=instance.project, number=instance.number)
    except ObjectDoesNotExist:
        return

    # unfollow/follow in archive/unarchive (activity stream)
    if not old.archived and instance.archived:
        for user in followers(instance.project):
            unfollow_issue(user, instance)
    if old.archived and not instance.archived:
        for user in followers(instance.project):
            follow_issue(user, instance)


@receiver(pre_save, sender=Issue)
def set_kanbancol(sender, instance, *args, **kwargs):
    instance.was_in_sprint = False


@receiver(pre_save, sender=Issue)
def set_kanbancol(sender, instance, *args, **kwargs):
    """
    This signal handler has to be the last one. Handlers are called in reverse
    order of connection and this handler is vital.
    """
    if not hasattr(instance, 'kanbancol'):
        instance.kanbancol = instance.project.kanbancol.first()
    # This is necessary for model mommy to work properly
    if instance.kanbancol.project.id != instance.project.id:
        instance.kanbancol = instance.project.kanbancol.first()
    return
