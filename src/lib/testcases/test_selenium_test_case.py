"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test.testcases import TestCase
from lib.selenium_test_case import SeleniumTestCase


class SeleniumTest(TestCase):
    def test_setup_and_teardown(self):
        # test if the selenium driver works
        SeleniumTestCase.setUpClass()
        SeleniumTestCase.tearDownClass()

    # TODO TESTCASE test if screenshots are made
    def test_error_screenshot(self):
        pass
