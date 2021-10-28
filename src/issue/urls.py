"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include

from issue import views
from timelog import views as tl_views
from gitintegration import views as repo_views
from common.urls import project_pattern
from issue.autocomplete import IssuePrioAutocompleteView,\
    IssueTypeAutocompleteView

app_name = 'issue'

issue_sqn_s_pattern = r'(?P<sqn_s>[0-9]+)'


urlpatterns = [
    url(r'^issue/', include([
        url(r'^$', views.IssueListAllView.as_view(), name='issue_list_all_view'),
        url(r'^prioac/?$', IssuePrioAutocompleteView.as_view(), name='prioac'),
        url(r'^typeac/?$', IssueTypeAutocompleteView.as_view(), name='typeac'),
    ])),
    url(r'^project/'+project_pattern+r'issue/', include([
        url(r'^create/?$', views.IssueCreateView.as_view(), name='create'),
        url(r'assigntome/?$', views.AssignIssueToMeView.as_view(), name='assigntome',),
        url(r'^rmfromme/?$', views.RemoveIssueFromMeView.as_view(), name='rmfromme',),
        url(r'^setkanbancol/?$', views.AddIssueToKanbancolView.as_view(), name='setkanbancol',),
        url(r'^archivecol/?$', views.ArchiveMultipleIssueView.as_view(), name='archivecol',),
        url(r'^archiveissue/?$', views.ArchiveSingleIssueView.as_view(), name='archiveissue',),
        url(r'^unarchiveissue/?$', views.UnArchiveSingleIssueView.as_view(), name='unarchiveissue',),
        url(r'^(?P<sqn_i>[0-9]+)/', include([
            url(r'^$', views.IssueDetailView.as_view(), name='detail'),
            url(r'^edit/?$', views.IssueEditView.as_view(), name='edit'),
            url(r'^delete/?$', views.IssueDeleteView.as_view(), name='delete'),
            url(r'^comment/(?P<pk_c>[0-9]+)/?$', views.IssueEditCommentView.as_view(), name='edit_comment'),
            url(r'^comment/(?P<pk_c>[0-9]+)/delete/?$', views.IssueDeleteCommentView.as_view(), name='delete_comment'),
            url(r'^attach/(?P<sqn_a>[0-9]+)/?$', views.AttachmentDownloadView.as_view(), name='download_attachment'),
            url(r'^attach/(?P<sqn_a>[0-9]+)/delete/?$', views.AttachmentDeleteView.as_view(), name='delete_attachment'),
            url(r'^log/?$', tl_views.TimelogCreateView.as_view(), name='log'),
            url(r'^punch/?$', tl_views.PunchView.as_view(), name='punch'),
            url(r'^logs/(?P<sqn_l>[0-9]+)/edit/?$', tl_views.TimelogEditView.as_view(), name='logedit'),
            url(r'^logs/(?P<sqn_l>[0-9]+)/delete/?$', tl_views.TimelogDeleteView.as_view(), name='logdelete'),
            url(r'diff/?$', repo_views.FileDiffView.as_view(), name='commit_diff'),
        ]))
    ]))
]
