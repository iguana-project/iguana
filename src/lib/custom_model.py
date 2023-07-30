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
from django.db import models
from abc import abstractmethod, ABCMeta

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.translation import ugettext as _


# It is very important to use this version to avoid extra checks on read-access.
# Therefore they need to imported from this file instead of the django.shortcuts version
# If a klass doesn't inherit from CustomModel there is no such function to check the permissions,
# which results in an error message.
def get_r_object_or_404(user, klass, *args, **kwargs):
    result = get_object_or_404(klass, *args, **kwargs)
    if not isinstance(result, CustomModel) or not result.user_has_read_permissions(user):
        raise Http404(_("Either the request object does not exist or you don't have the necessary " +
                        "permissions to access it."))
    return result


# returns 0 If object exists and user has read permission
# returns 1 Otherwise: either object doesn't exist or user doesn't have read permission on existing object
def has_r_object_or_zero(user, klass, *args, **kwargs):
    try:
        get_r_object_or_404(user, klass, *args, **kwargs)
    except Http404:
        return 0
    return 1


def get_w_object_or_404(user, klass, *args, **kwargs):
    result = get_object_or_404(klass, *args, **kwargs)
    if not isinstance(result, CustomModel) or not result.user_has_write_permissions(user):
        raise Http404(_("Either the request object does not exist or you don't have the necessary " +
                        "permissions to access it."))
    return result


# returns 0 If object exists and user has write permission
# returns 1 Otherwise: either object doesn't exist or user doesn't have write permission on existing object
def has_w_object_or_zero(user, klass, *args, **kwargs):
    try:
        get_w_object_or_404(user, klass, *args, **kwargs)
    except Http404:
        return 0
    return 1


class __AbstractModelMeta(ABCMeta, type(models.Model)):
    pass


class __ABCModel(models.Model, metaclass=__AbstractModelMeta):
    class Meta:
        abstract = True


class CustomModel(__ABCModel):
    class Meta:
        abstract = True

    @abstractmethod
    def user_has_read_permissions(self, user):
        """
        Call this method to check if a certain user has read permissions on an object of this model.

        It should return True if the user has the permissions, otherwise False.
        """
        raise NotImplementedError("Please Implement this method")

    @abstractmethod
    def user_has_write_permissions(self, user):
        """
        Call this method to check if a certain user has write permissions on an object of this model.

        It should return True if the user has the permissions, otherwise False.
        """
        raise NotImplementedError("Please Implement this method")

    def activity_stream_short_name(self):
        """
        The short name of this model for displaying in the activity stream.
        """
        return self.__str__()

    def activity_stream_long_name(self):
        """
        The long name of this model for displaying in the activity stream.
        """
        return self.__repr__()
