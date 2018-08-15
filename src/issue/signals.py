"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db.models.signals import post_save, m2m_changed, post_init, post_delete
from django.dispatch import receiver
from issue.models import Issue, Issue
from timelog.models import Punch
from sprint.models import Sprint

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key


def invalidate_cache(sender, instance, **kwargs):
    # remove duplicate signals if m2m changes

    if kwargs.get('action') == 'pre_add' or kwargs.get('action') == 'pre_remove':
        return

    # only delete board_template on column change
    fields = kwargs.get('update_fields')
    delete_backlog = True
    delete_board = True
    if fields and len(fields) == 1 and 'kanbancol' in fields:
        delete_backlog = False

    if isinstance(instance, Punch):
        issue = instance.issue
    else:
        issue = instance

    # invalidate cache templates only for the users involved
    user_list = issue.project.get_members()
    if sender == Issue.participant.through:
        user_list = user_list.filter(id__in=kwargs.get('pk_set'))
    if isinstance(instance, Punch):
        user_list = user_list.filter(id=instance.user.id)

    # invalidate backlog templates, if first noninactive sprint is created or last one gets deleted
    if isinstance(instance, Sprint):
        proj = instance.project
        count = proj.sprint.filter(enddate__isnull=True).count()
        if count > 1 or (count > 0 and not kwargs.get('created')):
            return
        delete_board = False
        issue = instance.project.issue.without_sprint().not_archived()
    else:
        issue = [issue]

    # delete cached templates for all users in project
    for iss in issue:
        for user in user_list:
            if delete_backlog:
                key = make_template_fragment_key('backlog_issue_template',
                                                 [iss.project.name_short, iss.number, user.username])
                cache.delete(key)

            if delete_board:
                key2 = make_template_fragment_key('board_issue_template',
                                                  [iss.project.name_short, iss.number, user.username])
                cache.delete(key2)


post_save.connect(invalidate_cache, sender=Issue, dispatch_uid="invalidate_issue_template.cards_post_save")
m2m_changed.connect(invalidate_cache, sender=Issue.tags.through,
                    dispatch_uid="invalidate_issue_template.cards_tags")
m2m_changed.connect(invalidate_cache, sender=Issue.assignee.through,
                    dispatch_uid="invalidate_issue_template.cards_assignee")
m2m_changed.connect(invalidate_cache, sender=Issue.participant.through,
                    dispatch_uid="invalidate_issue_template.cards_participant")
post_save.connect(invalidate_cache, sender=Punch,
                  dispatch_uid="invalidate_issue_template.cards_punch_post_init")
post_delete.connect(invalidate_cache, sender=Punch,
                    dispatch_uid="invalidate_issue_template.cards_punch_post_delete")
post_save.connect(invalidate_cache, sender=Sprint,
                  dispatch_uid="invalidate_issue_template.cards_punch_post_sprint")
