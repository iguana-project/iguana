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
from django.test.testcases import TestCase
from lib.selenium_test_case import SeleniumTestCase, \
    wait_after_function_execution
from datetime import datetime, timedelta


class TestDecoratorClass:
    def test_method(self, *args, **kwargs):
        pass


class SeleniumTest(TestCase):
    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.orig_test_method = TestDecoratorClass.test_method

    def tearDown(self):
        TestDecoratorClass.test_method = self.orig_test_method

    def call_test_method(self, *args, **kwargs):
        # create an instance of the test class and call its test method
        obj = TestDecoratorClass()
        start_time = datetime.utcnow()
        obj.test_method(*args, **kwargs)
        end_time = datetime.utcnow()

        # get the timedelta of the call and return it
        return end_time - start_time

    def test_setup_and_teardown(self):
        # test if the selenium driver works
        SeleniumTestCase.setUpClass()
        SeleniumTestCase.tearDownClass()

    # TODO TESTCASE test if screenshots are made
    def test_error_screenshot(self):
        pass

    def test_wait_decorator_without_condition(self):
        wait_time = 0.1

        # decorate function and call it
        TestDecoratorClass.test_method = wait_after_function_execution(wait_time)(TestDecoratorClass.test_method)
        diff_time = self.call_test_method()

        self.assertGreaterEqual(diff_time, timedelta(seconds=wait_time))

    def test_wait_decorator_with_condition_in_args(self):
        wait_time = 0.1
        found_arg = "test"
        not_found_arg = "not"
        TestDecoratorClass.test_method = wait_after_function_execution(wait_time, found_arg)(
            TestDecoratorClass.test_method
        )

        # condition fulfilled
        diff_time_fulfilled = self.call_test_method(not_found_arg, found_arg)
        self.assertGreaterEqual(diff_time_fulfilled, timedelta(seconds=wait_time))

        # condition not fulfilled
        diff_time_not_fulfilled = self.call_test_method()
        self.assertLess(diff_time_not_fulfilled, timedelta(seconds=wait_time))
        self.assertLess(diff_time_not_fulfilled, diff_time_fulfilled)

    def test_wait_decorator_with_condition_in_kwargs(self):
        wait_time = 0.1
        found_arg = "test"
        kwarg = {
            "not_iterable": 13,
            "not_found_arg": "not",
            "found_arg": found_arg,
        }
        TestDecoratorClass.test_method = wait_after_function_execution(wait_time, found_arg)(
            TestDecoratorClass.test_method
        )

        # condition fulfilled
        diff_time_fulfilled = self.call_test_method(**kwarg)
        self.assertGreaterEqual(diff_time_fulfilled, timedelta(seconds=wait_time))

        # condition not fulfilled
        diff_time_not_fulfilled = self.call_test_method()
        self.assertLess(diff_time_not_fulfilled, timedelta(seconds=wait_time))
        self.assertLess(diff_time_not_fulfilled, diff_time_fulfilled)
