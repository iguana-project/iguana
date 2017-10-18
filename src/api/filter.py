"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import rest_framework_filters as filters
from issue.models import Issue, Comment
from django.contrib.auth import get_user_model
from project.models import Project
from timelog.models import Timelog
from kanbancol.models import KanbanColumn
from timelog.forms import DurationField, DurationWidget


class DurationFilter(filters.Filter):
    field_class = DurationField
    widget = DurationWidget


class KanbanColumnFilter(filters.FilterSet):
    class Meta:
        model = KanbanColumn
        fields = ['type', 'name']


class UserFilter(filters.FilterSet):
    class Meta:
        model = get_user_model()
        fields = {
                'username': ['contains', 'exact']
                }


class IssueFilter(filters.FilterSet):
    status = filters.CharFilter(name='kanbancol__name', lookup_expr='exact')
    assignee = filters.CharFilter(name="assignee__username", lookup_expr='contains')
    participant = filters.CharFilter(name="participant__username", lookup_expr='contains')
    dependsOn = filters.NumberFilter(name="dependsOn__number", lookup_expr='exact')
    sprint = filters.NumberFilter(name="sprint__seqnum", lookup_expr='exact')
    project = filters.CharFilter(name="project__name_short", lookup_expr='exact')
    logged_total__gt = DurationFilter(name='logged_total', lookup_expr='gt')
    logged_total__lt = DurationFilter(name='logged_total', lookup_expr='lt')
    logged_total = DurationFilter(name='logged_total', lookup_expr='exact')

    class Meta:
        model = Issue
        fields = {
                'priority': ['exact', 'lt', 'gt'],
                'type': ['exact'],
                'description': ['contains'],
                'due_date': ['exact', 'lt', 'gt'],
                'created': ['exact', 'lt', 'gt'],
                'storypoints': ['exact', 'lt', 'gt'],
                'archived': ['exact'],
                'sprint': ['isnull']
                }


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = {
                'creator': ['exact'],
                'issue': ['exact'],
                'seqnum': ['exact', 'lt', 'gt'],
                'text': ['exact', 'contains'],
                'when': ['exact', 'lt', 'gt'],
                'modified': ['exact'],
                }


class TimelogFilter(filters.FilterSet):
    time__gt = DurationFilter(name='time', lookup_expr='gt')
    time__lt = DurationFilter(name='time', lookup_expr='lt')
    time = DurationFilter(name='time', lookup_expr='exact')

    class Meta:
        model = Timelog
        fields = {
                'user': ['exact'],
                'issue': ['exact'],
                'created_at': ['exact', 'lt', 'gt'],
                }
