"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from abc import abstractmethod, ABCMeta

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.translation import ugettext as _


# It is very important to use this version to avoid extra checks on read-access.
# Therefore one has to import from this file instead of the django.shortcuts version
# If klass doesn't inherit from CustomModel there is no such function to check the permissions,
# which results in an error message to be sure the programmer made decisions about that.
def get_r_object_or_404(user, klass, *args, **kwargs):
    result = get_object_or_404(klass, *args, **kwargs)
    if not isinstance(result, CustomModel) or not result.user_has_read_permissions(user):
        raise Http404(_("Either the request object does not exist or you don't have the necessary " +
                        "permissions to access it."))
    return result


def get_w_object_or_404(user, klass, *args, **kwargs):
    result = get_object_or_404(klass, *args, **kwargs)
    if not isinstance(result, CustomModel) or not result.user_has_write_permissions(user):
        raise Http404(_("Either the request object does not exist or you don't have the necessary " +
                        "permissions to access it."))
    return result


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
