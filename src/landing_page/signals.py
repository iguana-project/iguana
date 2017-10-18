"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save
from issue.models import Issue
from landing_page.actstream_util import follow_issue
from actstream.models import followers


@receiver(post_save, sender=Issue)
def auto_follow_issue_on_creation(sender, instance, created, *args, **kwargs):
    # test for a new issue
    if created and instance.creator:
        # the project followers follow the issue automatically
        for user in followers(instance.project):
            follow_issue(user, instance)
