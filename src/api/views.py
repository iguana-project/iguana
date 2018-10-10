"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, viewsets, mixins, reverse, permissions
from rest_framework.response import Response
from project.models import Project
from timelog.models import Timelog
from timelog.forms import TimelogCreateForm2
from .permissions import *
from .serializer import *
from django.contrib.auth import get_user_model
from django.http import Http404
import re


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    filter_class = UserFilter
    lookup_field = 'username'
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = get_user_model().objects.all()


class IssueViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    filter_class = IssueFilter
    serializer_class = IssueSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.issues


class TimelogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TimelogSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = TimelogFilter

    def get_queryset(self):
        return self.request.user.logged_on.all()


class NotificationViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'issue'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        temp = self.kwargs[lookup_url_kwarg].split('-')
        if len(temp) != 2 or not re.match('^[0123456789]+$', temp[1]):
            raise Http404
        project = temp[0]
        number = temp[1]
        filter_kwargs = {'issue__number': number, 'issue__project__name_short': project}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        return self.request.user.notifications.all()


class ProjectViewSet(viewsets.ModelViewSet):
    lookup_field = 'name_short'

    def get_queryset(self):
        return self.request.user.get_projects()

    def get_permissions(self):
        if self.action == 'list' or self.action == 'create':
            return [permissions.IsAuthenticated(), ]
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), UserIsMemberInProject()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), UserIsManagerInProject()]
        return [permissions.IsAuthenticated(), UserIsManagerInProject()]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'create']:
            return ProjectSerializer
        return ProjectUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(manager=[self.request.user, ], creator=self.request.user)


class ProjectIssuesViewSet(viewsets.ModelViewSet):
    permission_classes = (UserIsMemberInProject,)
    lookup_field = 'number'
    filter_class = IssueFilter

    def get_serializer_class(self):
        return IssueSerializer

    def get_queryset(self):
        queryset = Issue.objects.all()
        proj = self.kwargs.get('project', '')
        return queryset.filter(project__name_short=proj)

    def perform_create(self, serializer):
        project = self.kwargs.get('project', '')
        proj = Project.objects.filter(name_short=project).first()
        serializer.save(creator=self.request.user, project=proj)


class ProjectSprintsViewSet(viewsets.ModelViewSet):
    permission_classes = (UserIsMemberInProject,)
    lookup_field = 'seqnum'

    def get_serializer_class(self):
        return SprintSerializer

    def get_queryset(self):
        queryset = Sprint.objects.all()
        proj = self.kwargs.get('project', '')
        return queryset.filter(project__name_short=proj).unstopped()

    def perform_create(self, serializer):
        project = self.kwargs.get('project', '')
        proj = Project.objects.filter(name_short=project).first()
        serializer.save(project=proj)


class ProjectTimelogsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (UserIsMemberInProject, )
    filter_class = TimelogFilter

    def get_serializer_class(self):
        return TimelogSerializer

    def get_queryset(self):
        queryset = Timelog.objects.all()
        proj = self.kwargs.get('project', '')
        project = Project.objects.get(name_short=proj)
        if project.activity_only_for_managers and self.request.user not in project.manager.all():
            return queryset.filter(issue__project__name_short=proj, user=self.request.user)
        return queryset.filter(issue__project__name_short=proj)


class ProjectIssuesCommentsViewSet(viewsets.ModelViewSet):
    lookup_field = 'seqnum'
    filter_class = CommentFilter

    def get_serializer_class(self):
        return CommentSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [permissions.IsAuthenticated(), UserIsMemberInProject()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), UserIsOwnerOrManager()]
        return [permissions.IsAuthenticated(), UserIsOwnerOrManager()]

    def get_queryset(self):
        project = self.kwargs.get('project', '')
        issue = self.kwargs.get('issue', '')
        return Comment.objects.filter(issue__project__name_short=project, issue__number=issue)

    def get_issue(self):
        project = self.kwargs.get('project', '')
        issue = self.kwargs.get('issue', '')
        return Issue.objects.get(project__name_short=project, number=issue)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user, issue=self.get_issue())


class ProjectIssuesTimelogsViewSet(viewsets.ModelViewSet):
    lookup_field = 'number'
    filter_class = TimelogFilter

    def get_serializer_class(self):
        return TimelogSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [permissions.IsAuthenticated(), UserIsMemberInProject()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), UserIsOwnerOrManager()]
        return [permissions.IsAuthenticated(), UserIsOwnerOrManager()]

    def get_queryset(self):
        project = self.kwargs.get('project', '')
        issue = self.kwargs.get('issue', '')
        return Timelog.objects.filter(issue__project__name_short=project, issue__number=issue)

    def get_issue(self):
        project = self.kwargs.get('project', '')
        issue = self.kwargs.get('issue', '')
        return Issue.objects.get(project__name_short=project, number=issue)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, issue=self.get_issue())
