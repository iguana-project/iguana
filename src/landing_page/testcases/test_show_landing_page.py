"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.urls.base import reverse


class ShowLandingPageTest(TestCase):
    def test_show_landing_page_when_logged_out(self):
        response = self.client.get(reverse('landing_page:home'))
        self.assertTemplateUsed(response, "landing_page/home.html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "iguana")
