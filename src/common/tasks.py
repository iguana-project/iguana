"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from actstream.models import user_stream, actor_stream
from django.core.cache import cache
from lib.activity_permissions import check_activity_permissions
from django.contrib.auth import get_user_model
from discussion.models import Notification
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from common.settings import HOST
from django.core.mail import EmailMessage

import json


@shared_task
def update_activity_stream_for_user(user, actor=False):
    user = get_user_model().objects.get(username=user)
    if actor:
        item_list = actor_stream(user)
        cache.set('activity_items_actor_'+user.username, item_list, 60*60*24*31)
    else:
        item_list = check_activity_permissions(user, user_stream(user))
        cache.set('activity_items_'+user.username, item_list, 60*60*24*31)
    return


@shared_task
def send_discussion_mail(notification_pk):
    # check user profile for desired notification types (not yet existing)
    #   - this could maybe be done using a json-serialized dictionary assigning lists of notifications to project names
    #   - noti_<prj_shortname> -> [NewComment, NewIssue]
    #   - could also be stored in preferences store
    #   - not very efficient when changing desired notification types (table with checkboxes) (but not done very often)
    #   - new function in custom_user for storing/loading lists (json-serialized) in user preferences
    # send mail to user
    # for testing purpose this function returns int values to check for correct return points

    if len(Notification.objects.filter(pk=notification_pk)) != 1:
        # something went wrong with the given pk
        return 1

    noti = Notification.objects.get(pk=notification_pk)

    # check if user has mail address
    if not noti.user.email:
        return 2

    # find user's notification preferences for given project
    prefs = {}
    try:
        prefs = json.loads(noti.user.get_preference("notify_mail"))

    except (TypeError, json.JSONDecodeError):
        # already set to default value
        pass
    prefs_proj = prefs.get(noti.issue.project.name_short, [])

    needNotify = False

    for ntype in noti.type.all():
        # all types this notification contains
        if ntype.type in prefs_proj:
            needNotify = True
            break

    if not needNotify:
        # no notification necessary
        return 3

    actions = {
        'Mention': _('mentioned you in'),
        'NewComment': _('commented on'),
        'NewAttachment': _('attached a file to'),
        'EditComment': _('commented on'),
        'NewIssue': _('created'),
    }

    mail_body = render_to_string('mail-notification.txt',
                                 {'username': noti.user.get_username(),
                                  'project': noti.issue.project.name,
                                  'editor': 'Someone',  # this is a bit dirty :)
                                  'action': actions.get(noti.type.last().type, _('did something unknown')),
                                  'issue_name': noti.issue.title,
                                  'url': 'https://' + HOST + noti.issue.get_absolute_url(),
                                  })

    mail = EmailMessage("[Iguana] " + str(_('Notification from project')) + " \"" + noti.issue.project.name + "\"",
                        mail_body,
                        to=[noti.user.email])
    mail.send(True)
    return 0
