"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.template.response import TemplateResponse
import re


class csrfUpdateMiddleware(MiddlewareMixin):

    needs_update = ['issue/backlog_list.html', 'issue/sprintboard.html']

    def process_response(self, request, response):
        if isinstance(response, TemplateResponse) and response.template_name[0] in self.needs_update:
            content = response.content
            token = get_token(request)
            replace = b"name=\'csrfmiddlewaretoken\' value=\'" + token.encode() + b"\'"
            regex = re.compile(b"name=\'csrfmiddlewaretoken\'\s*value=\'\w*\'")
            response.content = re.sub(regex, replace, content)
        return response
