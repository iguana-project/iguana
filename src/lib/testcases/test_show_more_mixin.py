"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test.testcases import TestCase
from lib.show_more_mixin import ShowMoreMixin
from django.views.generic.base import TemplateView


test_items = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


class TempView(ShowMoreMixin, TemplateView):
    items_per_page = 2

    def __init__(self):
        # call the request method once for fulfilling coverage
        self.request()

    # add some additional required fields
    def request(self):
        return None
    setattr(request, 'method', 'POST')
    setattr(request, 'GET', 'page')


class ShowMoreMixinTest(TestCase):
    def setUp(self):
        self.tempView = TempView()

    def initialize_temp_view(self, page_string):
        self.tempView.item_list = test_items
        requestObj = self.tempView.__class__.__dict__['request']
        setattr(requestObj, 'GET', {'page': page_string})

    def test_empty_page_list(self):
        context = self.tempView.get_context_data(context1=1)
        self.assertIn('context1', context)

    def test_show_more(self):
        # request the first page
        self.initialize_temp_view("1")
        context = self.tempView.get_context_data()
        self.assertIn('page_items', context)

        # the first two items have to be in the list
        pi = context['page_items']
        self.assertEqual(pi.object_list, test_items[:2])

        # request the 3rd page
        self.initialize_temp_view("3")
        context = self.tempView.get_context_data()
        self.assertIn('page_items', context)

        # the first six items have to be in the list
        pi = context['page_items']
        self.assertEqual(pi.object_list, test_items[:6])

        # request a not existing page
        self.initialize_temp_view("10")
        context = self.tempView.get_context_data()
        self.assertIn('page_items', context)

        # all items have to be in the list
        pi = context['page_items']
        self.assertEqual(pi.object_list, test_items)

    def test_no_page_request(self):
        # request an invalid page
        self.initialize_temp_view("foo")
        context = self.tempView.get_context_data()
        self.assertIn('page_items', context)

        # the first page has to be returned
        pi = context['page_items']
        self.assertEqual(pi.number, 1)
