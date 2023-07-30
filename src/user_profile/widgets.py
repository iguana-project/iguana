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
from django.forms.widgets import ClearableFileInput
from django.contrib.auth import get_user_model
from django.db.models.fields.files import ImageFieldFile
from user_profile.apps import defaultAvatar


class CustomClearableFileInput(ClearableFileInput):
    defaultAvatar = None

    def value_from_datadict(self, data, files, name):
        value = super(CustomClearableFileInput, self).value_from_datadict(data, files, name)

        # value is false if the clear image check box is set
        if value is False:
            userModelAvatarField = get_user_model().avatar.field
            value = self.__class__.defaultAvatar = ImageFieldFile(instance=None,
                                                                  field=userModelAvatarField, name=defaultAvatar)

        return value

    def value_omitted_from_data(self, data, files, name):
        # the files field is empty if the default avatar is set
        if self.__class__.defaultAvatar:
            # so check for the name in data
            return name not in data

        return ClearableFileInput.value_omitted_from_data(self, data, files, name)

    def __del__(self):
        # clean up the default avatar again when this object is destroyed
        self.__class__.defaultAvatar = None

    @classmethod
    def isDefaultAvatar(cls, data):
        """
        Returns True if the provided data is the default avatar.
        """
        if cls.defaultAvatar is not None and cls.defaultAvatar == data:
            return True
        else:
            return False
