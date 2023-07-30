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
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.mixins import UserPassesTestMixin


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
