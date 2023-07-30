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
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase
from selenium import webdriver
from functools import wraps
from time import sleep
from selenium.webdriver.remote.webelement import WebElement
from django.conf import settings
from selenium.webdriver.common.keys import Keys
from collections.abc import Iterable


def wait_after_function_execution(wait_time=0, in_args=None):
    """
    Wait specified time in seconds after the execution of the function.
    Only wait if the 'in_args' value is found in the functions *args or **kwargs. Is ignored if 'in_args' is None.
    """
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            in_args_found = True
            if in_args:
                in_args_found = False
                for arg in args:
                    if isinstance(arg, Iterable) and \
                            in_args in arg:
                        in_args_found = True
                        break
                for value in kwargs.values():
                    if isinstance(value, Iterable) and \
                            in_args in value:
                        in_args_found = True
                        break

            # execute function
            result = func(*args, **kwargs)

            # wait..
            if in_args_found:
                sleep(wait_time)

            return result

        return wrapper
    return real_decorator


# monkey patch the WebElement class
# sometimes the browser needs some time to react to the clicking/submitting or KEY_RETURN event (executing JS, etc.)
WebElement.click = wait_after_function_execution(0.1)(WebElement.click)
WebElement.submit = wait_after_function_execution(0.2)(WebElement.submit)
WebElement.send_keys = wait_after_function_execution(0.2, in_args=Keys.RETURN)(WebElement.send_keys)


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
