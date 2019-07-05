"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from slackclient import SlackClient

from issue.models import Issue, Comment
from project.models import Project
from sprint.models import Sprint
from event import signals
from common.settings import HOST, DEBUG

from django.urls import reverse
from django.utils.translation import ugettext as _


class Integration(models.Model):
    project = models.ForeignKey(Project, models.CASCADE, verbose_name=_('project'))

    class Meta:
        abstract = True
        verbose_name = _("integration")
        verbose_name_plural = _("integrations")


class SlackIntegration(Integration):
    api_token = models.CharField(_("API token"), max_length=100)
    channel = models.CharField(_("channel"), max_length=100)
    notify_issue_create = models.BooleanField(_("notify on issue creation"), default=True)
    notify_issue_modify = models.BooleanField(_("notify on issue modification"), default=True)
    notify_comment_create = models.BooleanField(_("notify when there is a new comment"), default=True)
    notify_sprint_start = models.BooleanField(_("notify when a sprint is started"), default=True)
    notify_sprint_stop = models.BooleanField(_("notify when when a sprint is stopped"), default=True)
    slack = None

    class Meta:
        verbose_name = _("slackintegration")
        verbose_name_plural = _("slackintegrations")

    def __str__(self):
        return self.channel

    def connect_signals(self):
        if self.notify_issue_create:
            signals.create.connect(self.on_issue_signal, weak=False, sender=Issue)
        if self.notify_issue_modify:
            signals.modify.connect(self.on_issue_signal, weak=False, sender=Issue)
        if self.notify_comment_create:
            signals.create.connect(self.on_comment_signal, weak=False, sender=Comment)
        if self.notify_sprint_start:
            signals.start.connect(self.on_sprint_signal, weak=False, sender=Sprint)
        if self.notify_sprint_stop:
            signals.stop.connect(self.on_sprint_signal, weak=False, sender=Sprint)

    def disconnect_signals(self):
        if not self.notify_issue_create:
            signals.create.disconnect(self.on_issue_signal, sender=Issue)
        if not self.notify_issue_modify:
            signals.modify.disconnect(self.on_issue_signal, sender=Issue)
        if not self.notify_comment_create:
            signals.create.disconnect(self.on_comment_signal, sender=Comment)
        if not self.notify_sprint_start:
            signals.start.disconnect(self.on_sprint_signal, sender=Sprint)
        if not self.notify_sprint_stop:
            signals.stop.disconnect(self.on_sprint_signal, sender=Sprint)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.connect_signals()
        else:
            self.disconnect_signals()
        super(SlackIntegration, self).save(*args, **kwargs)

    def slack_on(self):
        if not self.slack:
            self.slack = SlackClient(self.api_token)

    def on_issue_signal(self, sender, signal, **kwargs):
        if "instance" not in kwargs or \
                kwargs['instance'].project != self.project:
            return
        self.slack_on()
        issue = kwargs['instance']
        user = kwargs['user']
        protocol = 'https://'
        if DEBUG:
            protocol = 'http://'
        title_link = protocol + HOST + issue.get_absolute_url()
        issue_title = issue.get_ticket_identifier() + ' ' + issue.title
        user_name = str(user)
        user_link = protocol + HOST + user.get_absolute_url()
        user_avatar = protocol + HOST + user.avatar.url

        if signal == signals.modify:
            text = '{} changed issue {}.'.format(user_name, issue_title)
            fields = []
            for field in kwargs['changed_data']:
                old_str = kwargs['changed_data'][field]
                new_field = issue.__getattribute__(field)
                new_str = str(new_field)
                # Ducktyping for RelatedManager
                if hasattr(new_field, "add") and \
                        hasattr(new_field, "create") and \
                        hasattr(new_field, "remove") and \
                        hasattr(new_field, "clear") and \
                        hasattr(new_field, "set"):
                    new_str = ", ".join([str(e) for e in new_field.all()])
                fields.append({
                    'title': Issue._meta.get_field(field).verbose_name.title(),
                    'value': '{} → {}'.format(old_str, new_str),
                    'short': True,
                })
                if field == 'description':
                    fields[-1]['short'] = False
            resp = self.slack.api_call(
                "chat.postMessage",
                channel=self.channel,
                attachments=[{
                    'fallback': text,
                    'pretext': 'Issue changed:',
                    'title': issue_title,
                    'title_link': title_link,
                    'author_name': user_name,
                    'author_link': user_link,
                    'author_icon': user_avatar,
                    'fields': fields,
                    'color': 'good',
                }]
            )
        elif signal == signals.create:
            text = '{} created issue {}.'.format(user_name, issue_title)
            resp = self.slack.api_call(
                "chat.postMessage",
                channel=self.channel,
                attachments=[{
                    'fallback': text,
                    'pretext': 'New Issue:',
                    'text': issue.description,
                    'title': issue_title,
                    'title_link': title_link,
                    'author_name': user_name,
                    'author_link': user_link,
                    'author_icon': user_avatar,
                    'color': 'good',
                }]
            )

    def on_comment_signal(self, sender, signal, **kwargs):
        if "instance" not in kwargs or \
                kwargs['instance'].issue.project != self.project:
            return
        self.slack_on()
        comment = kwargs['instance']
        user = kwargs['user']
        protocol = 'https://'
        if DEBUG:
            protocol = 'http://'
        title_link = protocol + HOST + comment.issue.get_absolute_url()
        issue_title = comment.issue.get_ticket_identifier() + ' ' + comment.issue.title
        user_link = protocol + HOST + user.get_absolute_url()
        user_avatar = protocol + HOST + user.avatar.url

        if signal == signals.create:
            text = '{} commented on "{}".'.format(str(user), issue_title)
            resp = self.slack.api_call(
                "chat.postMessage",
                channel=self.channel,
                attachments=[{
                    'fallback': text,
                    'pretext': 'New comment:',
                    'text': comment.text,
                    'title': issue_title,
                    'title_link': title_link,
                    'author_name': str(user),
                    'author_link': user_link,
                    'author_icon': user_avatar,
                    'color': 'good',
                }]
            )

    def on_sprint_signal(self, sender, signal, **kwargs):
        if "instance" not in kwargs or \
                kwargs['instance'].project != self.project:
            return
        self.slack_on()
        sprint = kwargs['instance']
        user = kwargs['user']
        protocol = 'https://'
        if DEBUG:
            protocol = 'http://'
        title_link = protocol + HOST + reverse("backlog:backlog", kwargs={'project': self.project.name_short})
        title = "sprint {}".format(sprint.seqnum)
        user_link = protocol + HOST + user.get_absolute_url()
        user_avatar = protocol + HOST + user.avatar.url

        action = ""
        text = ""
        if signal == signals.start:
            action = "started"
            text = '{} started {}.'.format(str(user), title)
        elif signal == signals.stop:
            action = "stopped"
            text = '{} stopped {}.'.format(str(user), title)
        title = title.capitalize()

        date_format = "%D"
        fields = []
        fields.append({
            'title': _("Started"),
            'value': sprint.startdate.strftime(date_format),
            'short': True,
        })
        if action == "stopped":
            fields.append({
                'title': _("Stopped"),
                'value': sprint.enddate.strftime(date_format),
                'short': True,
            })
        if sprint.plandate:
            fields.append({
                'title': _("Planned end"),
                'value': sprint.plandate.strftime(date_format),
                'short': True,
            })

        resp = self.slack.api_call(
            "chat.postMessage",
            channel=self.channel,
            attachments=[{
                'fallback': text,
                'pretext': 'Sprint {}:'.format(action),
                'text': '',
                'title': title,
                'title_link': title_link,
                'author_name': str(user),
                'author_link': user_link,
                'author_icon': user_avatar,
                'fields': fields,
                'color': 'good',
            }]
        )
