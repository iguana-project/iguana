"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db.models.query import QuerySet


def check_activity_permissions(user, actions):
    # the list of action PK that should be excluded from the list
    delActions = []

    # iterate over all actions
    for action in actions:
        # test if the user has permissions for the action_object
        if action.action_object is not None and not action.action_object.user_has_read_permissions(user):
            delActions.append(action.pk)
        # test if the user has permissions for the target object
        elif action.target is not None and not action.target.user_has_read_permissions(user):
            delActions.append(action.pk)

    # exclude the filtered actions from the actions
    actions = actions.exclude(pk__in=delActions)

    return actions
