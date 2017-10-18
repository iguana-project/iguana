"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase, override_settings
from django.conf.urls import url
from django.views.generic import View

from common.templatetags.breadcrumbs import breadcrumbs, Breadcrumb
from common.views import BreadcrumbView
from django.contrib.auth import get_user_model


class NotBreadcrumbView(View):
    breadcrumb = ""


class SubBreadcrumbView(BreadcrumbView):
    pass


urlpatterns = [
    url(r'^$', NotBreadcrumbView.as_view(breadcrumb="root")),
    url(r'^a/?$', NotBreadcrumbView.as_view(breadcrumb="layerone")),
    url(r'^a/b/c/?$', NotBreadcrumbView.as_view(breadcrumb="layertwo")),

    url(r'^1/?$', NotBreadcrumbView.as_view(breadcrumb="layerone")),
    url(r'^1/2/?$', NotBreadcrumbView.as_view(breadcrumb="")),
    url(r'^1/2/3/?$', NotBreadcrumbView.as_view(breadcrumb="layertwo")),

    url(r'^x/?$', NotBreadcrumbView.as_view(breadcrumb="layerone")),
    url(r'^x/y/?$', BreadcrumbView.as_view(breadcrumb="layertwo")),
    url(r'^x/y/z/?$', NotBreadcrumbView.as_view(breadcrumb="layerthree")),

    url(r'^n/?$', NotBreadcrumbView.as_view(breadcrumb="layerone")),
    url(r'^n/s/?$', SubBreadcrumbView.as_view(breadcrumb="layertwo")),
]


class DummyRequest():
    def __init__(self, path):
        self.path = path


@override_settings(ROOT_URLCONF='common.testcases.test_breadcrumbs')
class BreadcrumbsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('django', 'django@example.com', 'unchained')

    def setUp(self):
        self.client.force_login(self.user)

    def test_normal(self):
        """Check if breadcrumbs work and have proper urls."""
        context = {'request': DummyRequest("/a/b/c")}
        result = breadcrumbs(context)
        self.assertEqual(result, {
            'show': True,
            'breadcrumbs': [
                Breadcrumb('layerone', '/a/'),
                Breadcrumb('layertwo', '/a/b/c'),
            ],
        })

    def test_hiddenlayer(self):
        """Check if breadcrumb='' layers are truly hidden."""
        context = {'request': DummyRequest("/1/2/3")}
        result = breadcrumbs(context)
        self.assertEqual(result, {
            'show': True,
            'breadcrumbs': [
                Breadcrumb('layerone', '/1/'),
                Breadcrumb('layertwo', '/1/2/3'),
            ],
        })

    def test_breadcrumbview(self):
        """Check if BreadcrumbViews appear as layers without links."""
        context = {'request': DummyRequest("/x/y/z")}
        result = breadcrumbs(context)
        self.assertEqual(result, {
            'show': True,
            'breadcrumbs': [
                Breadcrumb('layerone', '/x/'),
                Breadcrumb('layertwo', ''),
                Breadcrumb('layerthree', '/x/y/z'),
            ],
        })

    def test_subclass(self):
        """Make sure subclasses of BreadcrumbView behave as such."""
        context = {'request': DummyRequest("/n/s")}
        result = breadcrumbs(context)
        self.assertEqual(result, {
            'show': True,
            'breadcrumbs': [
                Breadcrumb('layerone', '/n/'),
                Breadcrumb('layertwo', ''),
            ],
        })
