"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from actstream.actions import follow, unfollow
from django.core.cache import cache
from common.tasks import update_activity_stream_for_user


def follow_project(user, project):
    # follow the project
    follow(user, project, send_action=False, actor_only=False)
    # and all issues of this project
    for issue in project.issue.not_archived():
        follow_issue(user, issue)

    update_activity_stream_for_user.delay(user.username)
    update_activity_stream_for_user.delay(user.username, actor=True)


def unfollow_project(user, project):
    # unfollow the project
    unfollow(user, project)

    # and all of its issues
    for issue in project.issue.not_archived():
        unfollow_issue(user, issue)

    update_activity_stream_for_user.delay(user.username)
    update_activity_stream_for_user.delay(user.username, actor=True)


def follow_issue(user, issue):
    # follow an issue
    follow(user, issue, send_action=False, actor_only=False)


def unfollow_issue(user, issue):
    # unfollow an issue
    unfollow(user, issue)
