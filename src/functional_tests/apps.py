"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import inspect
import pkgutil
import sys

from django.apps import AppConfig
from django.test import tag

from lib.selenium_test_case import SeleniumTestCase


def getModules(parentPackageModule):
    """
    This method searches recursively through the packages and collects all Python modules.
    params:
        parentPackageModule: the package to start with
    """
    moduleList = []
    for _, moduleName, isPackage in pkgutil.iter_modules(parentPackageModule.__path__):
        fullModuleName = parentPackageModule.__name__ + '.' + moduleName

        # import of the module is necessary to access its members
        __import__(fullModuleName)
        moduleObject = sys.modules[fullModuleName]

        # check if the module is a package
        if isPackage:
            moduleList += getModules(moduleObject)
        else:
            moduleList.append(moduleObject)

    return moduleList


class FunctionalTestsConfig(AppConfig):
    name = 'functional_tests'

    def ready(self):
        # tag all functional tests with 'functional'
        # collect all modules of this package
        modules = getModules(sys.modules[self.name])

        # iterate over the moules
        for module in modules:
            # get the classes of the module
            clsmembers = inspect.getmembers(module, inspect.isclass)
            for clsName, cls in clsmembers:
                # check if it's a selenium test case
                if cls.__module__ == module.__name__ and \
                        issubclass(cls, SeleniumTestCase):
                    # tag it
                    setattr(module, clsName, tag("functional")(cls))
