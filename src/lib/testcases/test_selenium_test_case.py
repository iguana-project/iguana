"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test.testcases import TestCase
from lib.selenium_test_case import SeleniumTestCase, wait_for, decorateAllAssertFunctions
from lib import selenium_test_case
import time

# set the default timeout of for the selenium test cases to 5
selenium_test_case.DEFAULT_WAIT = 5
ASSERT_COUNT = 5


@wait_for
def delayAssert():
    global ASSERT_COUNT
    ASSERT_COUNT -= 1
    if not ASSERT_COUNT == 0:
        time.sleep(1)
        # raise ASSERT_COUNT times an exception, then succeed
        raise AssertionError


@decorateAllAssertFunctions(wait_for)
class TempTestAsserts(SeleniumTestCase):
    # this variable is just for checking if the decorator works
    assert_variable = "bla"

    firstCall = True

    def assert_function(self):
        # this function is just for checking if the decorator works
        # it should never be called
        raise NotImplementedError

    def assertWithParameter(self, param, posParam=None):
        if self.firstCall:
            self.firstCall = False
            raise AssertionError
        else:
            self.firstCall = True


class SeleniumTest(TestCase):
    def setUp(self):
        self.tempCase = TempTestAsserts()

    def test_setup_and_teardown(self):
        # test if the selenium driver works
        SeleniumTestCase.setUpClass()
        SeleniumTestCase.tearDownClass()

    def test_temporary_testcaseclass_works(self):
        self.tempCase.assertTrue(True)

    def test_multiline_assert(self):
        self.tempCase.assertWithParameter("This is a long string, " +
                                          "that makes no sense.")

    def test_quote_assert(self):
        self.tempCase.assertWithParameter("This parameter as a '")

    def test_positional_parameter_assert(self):
        self.tempCase.assertWithParameter("normal parameter", posParam="positional parameter")

    def test_assert_delayed(self):
        global ASSERT_COUNT
        ASSERT_COUNT = 2
        delayAssert()

    def test_assert_fails(self):
        global ASSERT_COUNT
        ASSERT_COUNT = 10
        self.assertRaises(AssertionError, delayAssert)

    def test_skip_timeout(self):
        selenium_test_case.SKIP_WRAPPING_TIMEOUT = True
        selenium_test_case.decorate(TempTestAsserts, wait_for, None)

        selenium_test_case.SKIP_WRAPPING_TIMEOUT = False
