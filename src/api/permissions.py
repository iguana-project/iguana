"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
