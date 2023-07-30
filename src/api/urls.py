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
