"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from functools import wraps
import linecache
import re
import sys
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement


DEFAULT_WAIT = 5
SKIP_WRAPPING_TIMEOUT = False


def decorate(cls, decoratorFunction, startWith):
    """
    This method replaces all functions that start with a given text of a class with a decorate function.
    """
    if not SKIP_WRAPPING_TIMEOUT:
        for name in dir(cls):
            # find all suitable methods
            if name.startswith(startWith):
                obj = getattr(cls, name)
                if callable(obj):
                    try:
                        obj = obj.__func__  # unwrap Python 2 unbound method
                    except AttributeError:
                        pass  # not needed in Python 3
                    # add the decorator to the method
                    setattr(cls, name, decoratorFunction(obj))
    return cls


def decorateAllAssertFunctions(decoratorFunction):
    """
    This method decorates all assert* methods of a class with the provided decorator function.
    """
    def decorator(cls):
        return decorate(cls, decoratorFunction, "assert")
    return decorator


def getParameters(frame):
    """
    The provided frame must point to a calling method.
    Then this method parses the method and returns its parameters as a list.
    """
    currentLineNo = frame.f_lineno
    # get the text at the given line number
    textLine = linecache.getline(frame.f_code.co_filename, currentLineNo).strip()
    # this stack is required for parsing the brackets (and later quotes)
    stack = []
    # in this list all read lines are entered
    textLines = [textLine]
    while True:
        # when the function spans across multiple lines the stack points always to the last line
        # so parse the string from end to beginning
        for i in reversed(range(0, len(textLine))):
            char = textLine[i]
            if char == ')' or \
                    char == "]" or \
                    char == '}':
                stack.append(char)
                continue
            if char == '(' or \
                    char == "[" or \
                    char == '{':
                stack.pop()
                continue
        # if there is something in the stack left, the function must be on multiple lines
        if stack:
            # decrease the line number and read it
            currentLineNo -= 1
            textLine = linecache.getline(frame.f_code.co_filename, currentLineNo).strip()
            # add the new line to the beginning of the line list
            textLines.insert(0, textLine)
        else:
            # if the stack is empty here, the function is completely parsed
            break

    # join all lines to the method call string
    methodStr = "".join(textLines)
    # remove outer brackets from method body
    parameterString = methodStr[methodStr.find("(") + 1:methodStr.rfind(")")]
    # in this stack all chars of a parameter are inserted
    paramStack = []
    # this is the final list that contains the parameters of the function
    parameters = []
    # parameters can be hard coded strings and theses strings can contain ','
    # so splitting by ',' is not possible to get the single parameters
    # but those strings must be captured either with '"' or with "'"
    # so it is possible to check if a ',' is surrounded by quotes
    for i in range(0, len(parameterString)):
        char = parameterString[i]
        # here the stack gets filled with eventual surrounding '"' or "'"
        if char == '"' or \
                char == "'":
            if not (char == '"' and stack and stack[-1] == "'") and \
                    not (char == "'" and stack and stack[-1] == '"'):
                if stack and \
                        stack[-1] == char:
                    stack.pop()
                else:
                    stack.append(char)
        # if a ',' was found and nothing is in the stack (-> ',' is not part of a string)
        # => a parameter has been found
        if char == ',' and \
                not stack:
            # add the parameter to the parameter list
            parameters.append("".join(paramStack).strip())
            paramStack = []
            continue
        paramStack.append(char)

    # add the last parameter also to the list
    if paramStack:
        parameters.append("".join(paramStack).strip())
    return parameters


def wait_for(function_with_assertion):
    @wraps(function_with_assertion)
    def wrapper(*args, **kw):
        """
        This wrapper is executed instead of the provided function.
        """
        start_time = time.time()
        while time.time() - start_time < DEFAULT_WAIT:
            try:
                return function_with_assertion(*args, **kw)
            except (AssertionError, WebDriverException):
                # wait a little bit
                time.sleep(0.1)

                # reload the arguments
                # get the calling method
                stackframe = sys._getframe().f_back
                # get the parameters of this method
                parameters = getParameters(stackframe)
                # create new *args and **kw
                if args and isinstance(args[0], SeleniumTestCase):
                    # the first argument is the instance
                    newArgs = (args[0],)
                else:
                    newArgs = ()
                newKw = {}
                # iterate over the parameter
                for param in parameters:
                    keyValueFound = False
                    for key in kw.keys():
                        # if the parameter is a positional parameter add it to the kw arguments
                        if param.startswith(key + "="):
                            param = re.sub(r'^.*=', '', param)
                            newKw[key] = eval(param, stackframe.f_globals, stackframe.f_locals)
                            keyValueFound = True

                    if not keyValueFound:
                        # special treatment for *args and **kwargs parameter
                        if param.startswith('**'):
                            param = re.sub(r'^(\*\*)', '', param)
                            newKw.update(eval(param, stackframe.f_globals, stackframe.f_locals))
                        elif param.startswith('*'):
                            param = re.sub(r'^(\*)', '', param)
                            newArgs += tuple(eval(param, stackframe.f_globals, stackframe.f_locals))
                        else:
                            # if it's a normal parameter add it to the args
                            newArgs += (eval(param, stackframe.f_globals, stackframe.f_locals),)
                # apply the new arguments
                args = newArgs
                kw = newKw
        return function_with_assertion(*args, **kw)
    return wrapper


# NOTE if this doesn't work, use
# "self.selenium.execute_script("arguments[0].scrollIntoView();", <element>)", where element is the
# actual element previusly searched by id or suchlike
def WebElement_click(self):
    """
    if element.click() fails with selenium.common.exceptions.WebDriverException, scroll down and try again
    """
    self.parent.execute_script("window.scrollTo(0, 0);")
    scroll = 20
    while scroll > 0:
        try:
            time.sleep(500.0 / 1000.0)
            WebElement.old_click(self)
            break
        except WebDriverException as e:
            if "Element is not clickable at point" in str(e):
                self.parent.execute_script("window.scrollBy(0, 100);")
                scroll = scroll - 1
                continue
            else:
                # reraise exception after enough tries
                self.parent.get_screenshot_as_file('screenshot.png')
                raise

# monkey patch the WebElement class
WebElement.old_click = WebElement.click
WebElement.click = WebElement_click


@decorateAllAssertFunctions(wait_for)
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
            cls.selenium = webdriver.Chrome()
        elif WEBDRIVER == "safari":
            cls.selenium = webdriver.Safari()
        else:
            raise Exception("Webdriver not configured probably!")
        cls.selenium.implicitly_wait(10)

        # wrap also the find_element(s)_by methods of the webdriver and webelement classes
        decorate(cls.selenium.__class__, wait_for, "find_element_by_")
        decorate(cls.selenium.__class__, wait_for, "find_elements_by_")
        decorate(WebElement, wait_for, "find_element_by_")
        decorate(WebElement, wait_for, "find_elements_by_")

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTestCase, cls).tearDownClass()


class StaticSeleniumTestCase(StaticLiveServerTestCase, SeleniumTestCase):
    """
    Extends SeleniumTestCase and provides staticfiles app automatically for the selenium tests.
    """
    pass
