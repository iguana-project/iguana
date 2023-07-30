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

from django.utils.translation import ugettext_lazy as _

NOT_PROJ_RELATED = "not related to any projects"


# This is pretty much just a logical hint for classes to be searchable.
# In most cases these functionalities are overwritten in the classes mixed this mixin in
class SearchableMixin():
    # NOTE: This shall be overwritten in the classes that mix this mixin in, otherwise this mixin is not useful there
    searchable_fields = []

    # This shall be overwritten in most of the classes that mix this mixin in
    def search_allowed_for_user(self, user):
        return True

    # when searching for a specific object type, this name is used by the parser to identify the class
    @classmethod
    def get_search_name(cls):
        return cls.__name__

    # This can be overwritten to use another function than __str__() as result title
    def get_search_title(self):
        return self.__str__()

    def get_relative_project(self):
        return _(NOT_PROJ_RELATED)
