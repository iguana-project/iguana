"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.mixins import UserPassesTestMixin
import mdx_urlize


"""
This file contains patches to the django source code.
TODO The patches in this file should be removed in the future and the default Django implementation should be used.
"""


# TODO If the test in the UserPassesTestMixin fails, the user should be redirected to the login page
# TODO with the warning that he has not the right permissions.
# TODO In the current Django implementation (2.2) if the test fails, a PermissionDenied (403) error is thrown.
# TODO The following patch reverts that change to the previous implementation.
def handle_no_permission(self):
    if self.raise_exception:
        raise PermissionDenied(self.get_permission_denied_message())
    return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())


UserPassesTestMixin.handle_no_permission = handle_no_permission


# TODO the regex matching of markdown-urlize is not working correctly
# TODO see https://github.com/r0wb0t/markdown-urlize/issues/16
# TODO replace it with a working pattern, thanks to https://mathiasbynens.be/demo/url-regex; thanks @stephenhay
mdx_urlize.URLIZE_RE = r"(%s)" % '|'.join([
    r"\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b",
    r"\b[^(<\s]+\.(?:com|edu|gov|int|mil|net|org|de)\b"  # use the domains from djangos built-in template tag urlize
])
