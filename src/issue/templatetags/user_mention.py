"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django import template
from django.db.models.query import QuerySet
register = template.Library()


@register.filter(name='user_list_for_mention')
def user_list_for_mention(users):
    """
    This template tag is used to convert a list of users to a dictionary, that is compatible with mention.js.
    """
    if isinstance(users, QuerySet):
        userlist = []
        for user in users:
            us = {}
            us['username'] = user.username
            us['image'] = user.avatar.url
            userlist.append(us)
        us = {}
        us['username'] = 'all'
        us['image'] = '/media/avatars/default.svg'
        userlist.append(us)
    return userlist
