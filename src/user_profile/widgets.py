"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
