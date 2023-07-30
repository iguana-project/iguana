"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
