"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django import template


register = template.Library()


@register.simple_tag(name='get_user_preference', takes_context=True)
def get_user_preference(context, key, default=None):
    user = context['user']
    return user.get_preference(key, default)
