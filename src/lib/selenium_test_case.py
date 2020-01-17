"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase
from selenium import webdriver
from functools import wraps
from time import sleep
from selenium.webdriver.remote.webelement import WebElement
from django.conf import settings


def wait_after_function_execution(func):
    """
    Wait 0.1 seconds after the execution of the function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        sleep(0.1)
        return result

    return wrapper


# monkey patch the WebElement class
# sometimes the browser needs some time to react to the clicking event (executing JS, etc.)
WebElement.click = wait_after_function_execution(WebElement.click)


class SeleniumTestCase(LiveServerTestCase):
    """
    SeleniumTestCase tries to provide a fix for selenium race conditions
    (wait_for) and overrides all assert methods from unittest.TestCase
    """
    processed_screenshots = []

    @classmethod
    def setUpClass(cls):
        super(SeleniumTestCase, cls).setUpClass()

        # load the webdriver setting as late as possible
        # this is needed when no web driver is specified and no functional tests should be run
        from common.settings.webdriver import WEBDRIVER

        if WEBDRIVER == "firefox":
            firefox_opt = None
            if settings.FUNCTESTS_HEADLESS_TESTING:
                firefox_opt = webdriver.FirefoxOptions()
                firefox_opt.headless = True
            cls.selenium = webdriver.Firefox(firefox_options=firefox_opt)
        elif WEBDRIVER == "chrome":
            chrome_opt = None
            if settings.FUNCTESTS_HEADLESS_TESTING:
                chrome_opt = webdriver.ChromeOptions()
                chrome_opt.headless = True
            cls.selenium = webdriver.Chrome(options=chrome_opt)
        elif WEBDRIVER == "safari":
            # headless mode is not possible right now in Safari
            # see https://github.com/SeleniumHQ/selenium/issues/5985
            cls.selenium = webdriver.Safari()
        else:
            raise Exception("Webdriver not configured probably!")
        cls.selenium.implicitly_wait(settings.FUNCTESTS_DEFAULT_WAIT_TIMEOUT)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTestCase, cls).tearDownClass()

    def __make_screenshot(self, _list, _type):
        for item in _list:
            # skip items whithout selenium attribute, because a screenshot can be made only of those
            if not hasattr(item[0], "selenium"):
                continue

            if hash(item) not in SeleniumTestCase.processed_screenshots:
                file_name = "%s - %s.png" % (_type, str(item[0]))
                self.selenium.get_screenshot_as_file(file_name)

                SeleniumTestCase.processed_screenshots.append(hash(item))
                break

    def run(self, result=None):
        res = LiveServerTestCase.run(self, result=result)

        # save screenshot of an error or failure
        if res.errors:
            self.__make_screenshot(res.errors, "Error")
        if res.failures:
            self.__make_screenshot(res.failures, "Failure")

        return res


class StaticSeleniumTestCase(StaticLiveServerTestCase, SeleniumTestCase):
    """
    Extends SeleniumTestCase and provides staticfiles app automatically for the selenium tests.
    """
    pass
