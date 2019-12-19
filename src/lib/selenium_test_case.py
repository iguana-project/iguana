"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase
from selenium import webdriver


DEFAULT_WAIT = 5


class SeleniumTestCase(LiveServerTestCase):
    """
    SeleniumTestCase tries to provide a fix for selenium race conditions
    (wait_for) and overrides all assert methods from unittest.TestCase
    """
    @classmethod
    def setUpClass(cls):
        super(SeleniumTestCase, cls).setUpClass()

        # load the webdriver setting as late as possible
        # this is needed when no web driver is specified and no functional tests should be run
        from common.settings.webdriver import WEBDRIVER

        if WEBDRIVER == "firefox":
            cls.selenium = webdriver.Firefox()
        elif WEBDRIVER == "chrome":
            # run Chrome in headless mode when testing on Travis
            chrome_opt = None
            if os.environ.get('TRAVIS') == 'true':
                chrome_opt = webdriver.ChromeOptions()
                chrome_opt.headless = True
            cls.selenium = webdriver.Chrome(options=chrome_opt)
        elif WEBDRIVER == "safari":
            cls.selenium = webdriver.Safari()
        else:
            raise Exception("Webdriver not configured probably!")
        cls.selenium.implicitly_wait(DEFAULT_WAIT)

        cls.processedScreenshots = []

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTestCase, cls).tearDownClass()

    def __make_screenshot(self, _list, _type):
        for item in _list:
            if hash(item) not in self.processedScreenshots:
                file_name = "%s - %s.png" % (_type, str(item[0]))
                self.selenium.get_screenshot_as_file(file_name)

                self.processedScreenshots.append(hash(item))
                break

    def run(self, result=None):
        res = LiveServerTestCase.run(self, result=result)

        # save screenshot of an error or failure
        if res.errors:
            self.__make_screenshot(res.errors, "Error")
        elif res.failures:
            self.__make_screenshot(res.errors, "Failure")

        return res


class StaticSeleniumTestCase(StaticLiveServerTestCase, SeleniumTestCase):
    """
    Extends SeleniumTestCase and provides staticfiles app automatically for the selenium tests.
    """
    pass
