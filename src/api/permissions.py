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
from rest_framework import permissions
from issue.models import Issue, Comment
from timelog.models import Timelog
from project.models import Project


class UserIsMemberInProject(permissions.BasePermission):

    def has_permission(self, request, view):
        project = view.kwargs.get('name_short', None)
        if not project:
            project = view.kwargs.get('project', None)
        if not project:
            return True
        proj = Project.objects.filter(name_short=project)
        if not proj.first():
            return False
        return proj.first().user_has_read_permissions(request.user)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Issue):
            proj = obj.project
        elif isinstance(obj, Timelog) or isinstance(obj, Comment):
            proj = obj.issue.project
        else:
            proj = obj
        return proj.user_has_read_permissions(request.user)


class UserIsManagerInProject(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.is_manager(request.user)


class UserIsOwnerOrManager(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Comment):
            if request.user == obj.creator or obj.issue.project.is_manager(request.user):
                return True
        if isinstance(obj, Timelog):
            if request.user == obj.user or obj.issue.project.is_manager(request.user):
                return True
        return False
