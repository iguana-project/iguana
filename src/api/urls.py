"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from api.views import IssueViewSet, ProjectIssuesViewSet, ProjectTimelogsViewSet, ProjectViewSet, NotificationViewSet
from api.views import TimelogViewSet, UserViewSet, ProjectIssuesCommentsViewSet, ProjectIssuesTimelogsViewSet
from api.views import ProjectSprintsViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from api.custom_jwt_auth import CustomTokenObtainPairView

from common.urls import project_pattern, project_pattern_optional, issue_pattern
app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'timelogs', TimelogViewSet, 'timelogs')
router.register(r'notifications', NotificationViewSet, 'notifications')
router.register(r'issues', IssueViewSet, 'issues')
router.register(r'projects', ProjectViewSet, 'project')
router.register(r'projects/' + project_pattern+r'timelogs', ProjectTimelogsViewSet, 'project_timelogs')
router.register(r'projects/' + project_pattern+r'issues', ProjectIssuesViewSet, 'project_issues')
router.register(r'projects/' + project_pattern+r'sprints', ProjectSprintsViewSet, 'project_sprints')
router.register(r'projects/' + project_pattern+r'issues/'+issue_pattern+r'comments',
                ProjectIssuesCommentsViewSet, 'project_issues_comments')
router.register(r'projects/' + project_pattern+r'issues/'+issue_pattern+r'timelogs',
                ProjectIssuesTimelogsViewSet, 'project_issues_timelogs')
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    url(r'^token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
