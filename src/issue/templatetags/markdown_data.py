"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django import template
from common.templatetags.markdownify import IssueExtension, UserExtension
from django.urls.base import reverse
from cuser.middleware import CuserMiddleware
register = template.Library()


@register.filter
def get_issue_markdown_data(project):
    max_ticket_number = project.nextTicketId - 1
    url = reverse('issue:detail', kwargs={'project': project.name_short, 'sqn_i': max_ticket_number})
    url = url[::-1].replace(str(max_ticket_number)[::-1], "<issue_number>"[::-1], 1)[::-1]
    data = {
        "re_pattern": IssueExtension.create_issue_pattern(project),
        "max_ticket_number": max_ticket_number,
        "issue_url": url,
    }
    return data


@register.filter
def get_user_markdown_data(project):
    current_username = CuserMiddleware.get_user().username
    url = reverse('user_profile:user_profile_page', kwargs={'username': current_username})
    url = url[::-1].replace(current_username[::-1], "<user_name>"[::-1], 1)[::-1]
    data = {
        "re_pattern": UserExtension.create_user_pattern(project),
        "user_url": url,
    }
    return data
