"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import activate

from common import urls
from django.contrib.auth import get_user_model


def list_names():
    def run(urllist, ln=[]):
        for entry in urllist:
            if hasattr(entry, "name"):
                ln.append(entry.name)
            if hasattr(entry, 'url_patterns'):
                run(entry.url_patterns, ln)
        return ln
    return run(urls.urlpatterns)


class GetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('django', 'django@example.com', 'unchained')

    def setUp(self):
        self.client.force_login(self.user)

    def compare(self, name):
        activate("en")
        en = self.client.get(reverse(name))
        activate("de")
        de = self.client.get(reverse(name))
        self.assertEqual(en.status_code, de.status_code)

    def test_urls(self):
        for name in list_names():
            try:
                reverse(name)
            except NoReverseMatch:
                continue
            self.compare(name)
