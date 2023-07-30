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
from rest_framework import generics, serializers, viewsets, mixins, reverse
from project.models import Project
from timelog.models import Timelog
from issue.models import Comment
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from timelog.forms import DurationField
from timelog.forms import DurationWidget
from timelog.templatetags.filter import duration
from lib.rattr import *


class TimelogLimitedField(serializers.CharField):
    def to_internal_value(self, data):
        # We're lenient with allowing basic numerics to be coerced into strings,
        # but other types should fail. Eg. unclear if booleans should represent as `true` or `True`,
        # and composites such as lists are likely user error.
        f = DurationField()
        return f.to_python(data)

    def to_representation(self, value):
        f = DurationWidget()
        return f.format_value(value)


class IssueLimitedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.issues.all()

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return value.project.name_short+"-"+str(value.number)+" "+value.title


class IssueLimitedFieldInProject(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('project'))
        return proj.first().issue.all()

    def to_representation(self, value):
        return value.project.name_short+"-"+str(value.number)+" "+value.title

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(number=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class LimitedTagFieldProject(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('project'))
        return proj.first().tags.all()

    def to_representation(self, value):
        return value.tag_text

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(tag_text=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class LimitedUserFieldProject(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('project'))
        return proj.first().get_members()

    def to_representation(self, value):
        return value.username

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(username=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class LimitedSprintFieldProject(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('name_short'))
        if proj.first() is None:
            proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('project'))
        return proj.first().sprint.all()

    def to_representation(self, value):
        return "Sprint-"+str(value.seqnum)

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(seqnum=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class LimitedColsFieldProject(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('project'))
        return proj.first().kanbancol.all()

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(name=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class LimitedColsFieldProject(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        proj = Project.objects.filter(name_short=self.context['view'].kwargs.get('project'))
        return proj.first().kanbancol.all()

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(name=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class MultiplePKsHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    lookup_fields = ['pk']

    def __init__(self, view_name=None, **kwargs):
        self.lookup_fields = kwargs.pop('lookup_fields', self.lookup_fields)
        self.lookup_url_kwargs = kwargs.pop('lookup_url_kwargs', self.lookup_fields)

        assert len(self.lookup_fields) == len(self.lookup_url_kwargs)

        super(MultiplePKsHyperlinkedIdentityField, self).__init__(view_name, **kwargs)

    def get_object(self, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.
        Takes the matched URL conf arguments, and should return an
        object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup_kwargs = {
            key: view_kwargs[url_key]
            for key, url_key in zip(self.lookup_fields, self.lookup_url_kwargs)
        }
        return self.get_queryset().get(**lookup_kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.
        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk is None:
            return None
        kwargs = {}
        for key, url_key in zip(self.lookup_fields, self.lookup_url_kwargs):
            kwargs[url_key] = rgetattr(obj, key)
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)
