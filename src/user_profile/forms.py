"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import CharField, PasswordInput, ValidationError
from django.forms.models import ModelForm
from django.forms.fields import ImageField
from django.forms.widgets import ClearableFileInput
from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UsernameField
from django.db.models.fields.files import ImageFieldFile

import os

from user_profile.apps import defaultAvatar
from common.settings import MEDIA_ROOT

from django.utils.translation import ugettext_lazy as _

from image_strip.image_strip import strip_img_metadata


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


class CustomImageField(ImageField):
    widget = CustomClearableFileInput

    def __init__(self, *args, **kwargs):
        kwargs["required"] = False
        super(CustomImageField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        # return the data if it is the default avatar
        if CustomClearableFileInput.isDefaultAvatar(data):
            self.validators = []
            return data

        return super(CustomImageField, self).to_python(data)


class CustomUserChangeForm(ModelForm):
    """
    Basically copied from UserChangeForm
    """
    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'avatar', 'language', 'timezone', 'show_activity_to_other_users')

        field_classes = {
            'username': UsernameField,
            'avatar': CustomImageField,
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserChangeForm, self).__init__(*args, **kwargs)
        # TODO The following lines were copied from UserChangeForm but are not used in any test or application.
        #      They can be removed later.
        # f = self.fields.get('user_permissions')
        # if f is not None:
        #     f.queryset = f.queryset.select_related('content_type')

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        return strip_img_metadata(avatar)

    def save(self, *args, **kwargs):
        """
        Override save() method to catch the changes for the avatar field
        """
        # get the old avatar file path and name
        old_avatar_filepath = os.path.join(MEDIA_ROOT, kwargs.pop('old_avatar_name'))
        old_avatar_name = os.path.basename(old_avatar_filepath)
        # get the new avatar file name
        new_avatar_name = os.path.basename(self.cleaned_data['avatar'].name)

        # if the names differ, delete the old file
        if old_avatar_name != new_avatar_name and \
                old_avatar_name != os.path.basename(defaultAvatar):
            os.path.exists(old_avatar_filepath) and os.remove(old_avatar_filepath)

        # instance.save()
        return super(CustomUserChangeForm, self).save(*args, **kwargs)


class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = get_user_model()

    # remove required tag from all password fields
    old_password = CharField(
        required=False,
        label=_("Old password"),
        strip=False,
        widget=PasswordInput,
    )
    new_password1 = CharField(
        required=False,
        label=_("New password"),
        widget=PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = CharField(
        required=False,
        label=_("New password confirmation"),
        strip=False,
        widget=PasswordInput,
    )

    def clean_old_password(self):
        # check if the old password field is empty
        data = self.cleaned_data
        o_pw = ""
        # needed for recheck
        n_pw1 = ""
        n_pw2 = ""
        if 'old_password' in data:
            o_pw = data['old_password']
        if 'new_password1' in data:
            n_pw1 = data['new_password1']
        if 'new_password2' in data:
            n_pw2 = data['new_password2']
        # old password is filled
        # It is very important to check this even if the new-pw-fields are empty
        # otherwise the save function would be called and with empty new-pw-fields this results in empty new pw,
        # which is a catastrophe because our login page requires it to enter a passwords with length of 8 or more
        # so a user would be locked out forever.
        if o_pw != "":
            return super(CustomPasswordChangeForm, self).clean_old_password()
        # old pw is wrong (during second check) or is not filled and at least one of the new password fields is filled
        elif n_pw1 != "" or n_pw2 != "":
            # we need to add this entry to be able to call the super clean function
            self.cleaned_data['old_password'] = ''
            return super(CustomPasswordChangeForm, self).clean_old_password()
        # none of the fields is filled yet. NOTE: n_pw1 or n_pw2 might be filled during second check (s. clean())
        else:
            return o_pw

    def clean_new_password2(self):
        # only proceed this field if old password field is not empty
        data = self.cleaned_data
        n_pw1 = ""
        n_pw2 = ""
        if 'new_password1' in data:
            n_pw1 = data['new_password1']
        if 'new_password2' in data:
            n_pw2 = data['new_password2']
        # at least one of new-pw-field is filled
        if n_pw2 == "":
            self.cleaned_data['new_password2'] = ""
        if n_pw1 != "" or n_pw2 != "":
            new_pw2 = super(CustomPasswordChangeForm, self).clean_new_password2()
            # somehow this is not checked in super-method if n_pw1 is empty
            if n_pw1 != new_pw2:
                raise ValidationError(_("The two password fields didn't match."))
            return new_pw2
        # both new-pw-fields are empty
        else:
            return n_pw2

    def clean(self):
        cleaned_data = super(CustomPasswordChangeForm, self).clean()
        n_pw1 = ""
        n_pw2 = ""
        o_pw = ""
        if 'new_password1' in cleaned_data:
            n_pw1 = cleaned_data['new_password1']
        if 'new_password2' in cleaned_data:
            n_pw2 = cleaned_data['new_password2']
        if 'old_password' in cleaned_data:
            o_pw = cleaned_data['old_password']

        if n_pw1 != "" or n_pw2 != "":
            # ERROR case!
            # 1. Either old one is not entered => call relative clean-function with cleaned new-pw-fields
            # => second run for clean old_password => now it fails
            # 2. or the old-pw-field was filled and is already cleaned but was wrong => it is empty now
            if o_pw == "":
                old_clean = self.clean_old_password()
                # update the value of the dict (important!)
                cleaned_data['old_password'] = old_clean
                return cleaned_data
            # ERROR case! one of the new-pw-fields was empty or wrong and is empty now because of the field-clean
            elif n_pw1 == "" or n_pw2 == "":
                raise ValidationError(_("Either the two password fields didn't match or additional " +
                                        "restrictions are not fullfilled."))
            # old-pw-field is not empty and is valid (already has been cleaned and would be empty otherwise)
            else:
                return cleaned_data
        # don't change the password
        # 1. Either none of the new pw fields is filled
        # 2. or it might be that the old password was entered wrongly, but that doesn't matter,
        # because it has been verified already and fails in case of a wrong pw => save() is not called
        # 3. or or the old-pw was entered correctly, but none of the new-pw-fields => redirect to users page without
        # storing the new pw (would be empty then)
        # NOTE: this case is not perfect, because it redirects to users page even though only
        #       the old password was entered, but well.
        else:
            # mark the CustomPasswordChangeForm as valid because it has not been used.
            # This is necessary to save the other forms in this multiform
            self.cleaned_data['not_validated'] = "1"
            if 'new_password1' in cleaned_data and cleaned_data['new_password1'] == '':
                del cleaned_data['new_password1']
            return cleaned_data

    def save(self, commit=True):
        # check if an old pw is provided before changing it
        cleaned_data = self.cleaned_data
        # the password change form was not filled so we redirect to the users page
        if 'not_validated' in cleaned_data:
            return self.user

        # invalid password change tries
        # happend in super clean
        # ok
        else:
            return super(CustomPasswordChangeForm, self).save(commit)
