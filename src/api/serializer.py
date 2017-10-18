"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from issue.models import Issue, Comment
from rest_framework import generics, serializers, viewsets, mixins, reverse
from rest_framework.response import Response
from project.models import Project
from sprint.models import Sprint
from timelog.models import Timelog
from timelog.forms import TimelogCreateForm2, DurationWidget
from discussion.models import Notification

from .permissions import *
from .filter import *
from .serializer_fields import *
from django.contrib.auth import get_user_model
import datetime


class UserSerializer(serializers.ModelSerializer):
    url = MultiplePKsHyperlinkedIdentityField(
        view_name='api:customuser-detail',
        lookup_fields=['username'],
        lookup_url_kwargs=['username']
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'url', 'first_name', 'last_name')


class SprintSerializer(serializers.ModelSerializer):
    def get_issues(self, obj):
        return [issue.project.name_short+"-"+str(issue.number) for issue in obj.issue.all()]
    issues = serializers.SerializerMethodField()

    def get_project(self, obj):
        return obj.project.name_short

    project = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = ('seqnum', 'project', 'startdate', 'enddate', 'issues')


class IssueSerializer(serializers.ModelSerializer):

    def get_project_members(self, obj):
        return [user.username for user in obj.project.get_members()]

    def get_project_cols(self, obj):
        return [col.name for col in obj.project.kanbancol.all()]

    def get_project_tags(self, obj):
        return [(tag.tag_text, tag.color, tag.font_color) for tag in obj.project.tags.all()]

    project = serializers.StringRelatedField()
    creator = LimitedUserFieldProject(required=False, read_only=True)
    tags = LimitedTagFieldProject(many=True, read_only=False, required=False)
    assignee = LimitedUserFieldProject(many=True, required=False)
    participant = LimitedUserFieldProject(many=True, required=False)
    dependsOn = IssueLimitedFieldInProject(many=True, required=False)
    kanbancol = LimitedColsFieldProject(required=False)
    sprint = LimitedSprintFieldProject(required=False, allow_null=True)
    logged_total = TimelogLimitedField(required=False, read_only=True)
    project_members = serializers.SerializerMethodField()
    project_cols = serializers.SerializerMethodField()
    project_tags = serializers.SerializerMethodField()
    archived = serializers.BooleanField(required=False)
    url = MultiplePKsHyperlinkedIdentityField(
        view_name='api:project_issues-detail',
        lookup_fields=['project.name_short', 'number'],
        lookup_url_kwargs=['project', 'number']
    )

    class Meta:
        model = Issue
        exclude = ('id', 'nextCommentId', 'nextAttachmentId', 'nextTimelogId')
        read_only_fields = ('project', )


class TimelogSerializer(serializers.ModelSerializer):
    issue = IssueLimitedField(required=False)
    user = serializers.StringRelatedField()
    time = TimelogLimitedField()
    url = MultiplePKsHyperlinkedIdentityField(
        view_name='api:project_issues_timelogs-detail',
        lookup_fields=['issue.project.name_short', 'issue.number', 'number'],
        lookup_url_kwargs=['project', 'issue', 'number']
    )

    class Meta:
        model = Timelog
        form = TimelogCreateForm2
        exclude = ('id',)
        read_only_fields = ('user', 'issue')


class NotificationSerializer(serializers.ModelSerializer):
    issue = IssueLimitedField(required=False)
    user = serializers.StringRelatedField()
    type = serializers.StringRelatedField(many=True)

    class Meta:
        model = Notification
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    issue = serializers.StringRelatedField()
    creator = serializers.StringRelatedField()
    url = MultiplePKsHyperlinkedIdentityField(
        view_name='api:project_issues_comments-detail',
        lookup_fields=['issue.project.name_short', 'issue.number', 'seqnum'],
        lookup_url_kwargs=['project', 'issue', 'seqnum']
        )

    class Meta:
        model = Comment
        exclude = ('id', )
        read_only_fields = ('when', 'creator', 'modified', 'issue', 'issue', 'seqnum')


class ProjectSerializer(serializers.ModelSerializer):
    manager = serializers.SlugRelatedField(many=True, queryset=get_user_model().objects.all(),
                                           slug_field='username', required=False, allow_null=True)
    developer = serializers.SlugRelatedField(many=True, queryset=get_user_model().objects.all(),
                                             slug_field='username', required=False, allow_null=True)
    creator = serializers.StringRelatedField(
            default=serializers.CurrentUserDefault()
            )
    kanbancol = serializers.StringRelatedField(many=True, read_only=True)
    url = MultiplePKsHyperlinkedIdentityField(
        view_name='api:project-detail',
        lookup_fields=['name_short'],
        lookup_url_kwargs=['name_short']
        )
    currentsprint = LimitedSprintFieldProject(required=False, allow_null=True)

    def get_sprints(self, obj):
        return [SprintSerializer(sprint).data for sprint in obj.sprint.unstopped()]

    sprints = serializers.SerializerMethodField()

    def get_tags(self, obj):
        return [(tag.tag_text, tag.color, tag.font_color) for tag in obj.tags.all()]

    tags = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ('id', 'nextTicketId', 'nextSprintId', 'activity')
        read_only_fields = ('creator',)


class ProjectUpdateSerializer(serializers.ModelSerializer):
    manager = serializers.SlugRelatedField(many=True, queryset=get_user_model().objects.all(),
                                           slug_field='username', required=False, allow_null=True)
    developer = serializers.SlugRelatedField(many=True, queryset=get_user_model().objects.all(),
                                             slug_field='username', required=False, allow_null=True)
    creator = serializers.StringRelatedField(
            default=serializers.CurrentUserDefault()
            )
    kanbancol = serializers.StringRelatedField(many=True, read_only=True)
    url = MultiplePKsHyperlinkedIdentityField(
        view_name='api:project-detail',
        lookup_fields=['name_short'],
        lookup_url_kwargs=['name_short']
        )
    currentsprint = LimitedSprintFieldProject(required=False, allow_null=True)

    def validate_manager(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("A Project needs at least one manager")
        return value

    class Meta:
        model = Project
        exclude = ('id', 'nextTicketId', 'nextSprintId', 'activity')
        read_only_fields = ('creator', 'name_short')
